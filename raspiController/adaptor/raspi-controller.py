#!/usr/bin/env python3
# -*- coding: utf-8 -*-

'''
This is adaptor for Raspberry PI GPIO controller
'''

import sys
import logging
import time
import pathlib
import threading
import datetime as dt

scriptPath = pathlib.Path(__file__).parent.resolve()
sys.path.append(str(scriptPath.parent / 'common'))
from adaptor import Adaptor

DEBUG = True
if DEBUG:
    FAKE_STAT = {
        'power': 0,
        'red': 0,
        'amber': 0,
        'green': 0,
    }
else:
    import RPi.GPIO as GPIO
CHN = {
    'power': 26,
    'red': 23,
    'amber': 24,
    'green': 25,
}
ALERT_IN = {
    'alert': 6,
}
ALERT_OUT = {
    'pwm': 18,
}

class RaspiController(Adaptor):
    def __init__(self, args, **kw) -> None:
        self.alert = False

        if not DEBUG:
            GPIO.setwarnings(False)
            GPIO.setmode(GPIO)
            for chn, pin in CHN.items:
                GPIO.setup(pin, GPIO.OUT)
                logging.debug('Set {} pin {} as output'.format(chn, pin))
            for chn, pin in ALERT_IN.items:
                GPIO.setup(pin, GPIO.IN)
                logging.debug('Set {} pin {} as alert input'.format(chn, pin))
            for chn, pin in ALERT_OUT.items:
                GPIO.setup(pin, GPIO.OUT)
                logging.debug('Set {} pin {} as alert output'.format(chn, pin))

        Adaptor.__init__(self, args, **kw)
        self.subscribe_channels = [
            '{}.result'.format(self.component_prefix),
            '{}.alert'.format(self.component_prefix)
        ]
        self.start_listen_bus()
        self.save_info()
    
    def start (self, **extra_kw):
        ''' start raspberry pi module '''
        self._init_power()

        self.th_switch_quit = threading.Event()
        self.th_switch = threading.Thread(target=self.alert_switch_capture)
        self.th_switch.start()

    def _init_power (self):
        ''' init power light and update status '''
        self.set_gpio_status('power', 'low')       
        _status = 'success' if self.get_gpio_status('power') == 0 else 'failed'
        Adaptor.publish_msg(
            self,
            'response', 
            {'stage': 'init', 'status': _status}
        )
        logging.debug('Init Power {}'.format(_status))

    def alert_switch_capture (self):
        ''' alert switch capture thread'''
        while True:
            if not DEBUG:
                if GPIO.input(ALERT_IN['alert']) == GPIO.HIGH:
                    if self.alert:
                        logging.debug('Switch pressed to reset alert')
                        self.alert_reset()
                    else:
                        logging.debug('Switch pressed to enable alert')
                        self._process_alert_msg(
                            {'stage': 'alert', 'status': 'activated'},
                            bySwitch=True
                        )
            if self.th_switch_quit.is_set():
                break

    def alert_reset (self):
        ''' reset alert when self.alert == True and switch pressed'''
        _result = True
        self.set_gpio_status('amber', 'low')
        _out = 'low' if self.get_gpio_status('amber') == 0 else 'high'
        if _out != 'low': _result = False
        logging.debug('[alert-reset]: LED amber set to low: {}'.format(_result))
        if _result: self.alert = False
        Adaptor.publish_msg(
            'alert-response',
            {'stage': 'alert-response', 'status': 'success' if _result else 'failed'}
        )
        logging.debug('[alert-reset] response: {}'.format('success' if _result else 'failed',))

    def process_redis_msg(self, ch, msg):
        ''' process received redis message'''
        if ch in self.subscribe_channels:
            logging.debug('[{}]: ch: {}, msg: {}'.format(self, ch, msg))
            if ch == '{}.result'.format(self.component_prefix):
                self.process_result_msg(msg)
            if ch == '{}.alert'.format(self.component_prefix):
                self._process_alert_msg(msg)

    def _process_result_msg (self, msg):
        ''' process normal result msg'''
        _stage = msg.get('stage', 'error')
        if _stage == 'beginCapture':
            self._stage_change(msg, chns={'red': 'low', 'amber': 'low', 'green': 'low'})
        elif _stage == 'testScreen':
            self._stage_change(msg, chns={'red': 'high', 'amber': 'low', 'green': 'low'})
        elif _stage == 'popUp':
            self._stage_change(msg, chns={'red': 'high', 'amber': 'low', 'green': 'high'})

    def _process_alert_msg (self, msg, bySwitch=False):
        ''' process alert msg '''
        _status = msg.get('status', 'deactivate')
        _stage = msg.get('stage', 'error')
        if _stage == 'error':
            logging.error('Unable to determine stage {}'.format(_stage))
            return
        if _status == 'activated':
            _result = True
            self.set_gpio_status('amber', 'high')
            
            self._servo_change()

            _out = 'low' if self.get_gpio_status('amber') == 0 else 'high'
            if _out != 'high':
                _result = False
            logging.debug('[{}]: LED amber set to high: {}'.format(_stage, _result))
            Adaptor.publish_msg(
                'alert-response',
                {'stage': 'alert-switch' if bySwitch else 'alert-msg',
                 'status': 'success' if _result else 'failed'}
            )
            logging.debug('[{}] response: {}'.format(_stage, 'success' if _result else 'failed'))   

    def _stage_change (self, msg, chns={}):
        ''' process begin capture & test screen & pop up 
            chns format should be: {'key': 'low'|'high' ... }
        '''
        _status = msg.get('status', 'failed')
        _stage = msg.get('stage', 'error')
        if _stage == 'error':
            logging.error('Unable to determine stage {}'.format(_stage))
            return
        if _status == 'success':
            _result = True
            for chn, val in chns.items():
                self.set_gpio_status(chn, val)
                _out = 'low' if self.get_gpio_status(chn) == 0 else 'high'
                if _out != val: 
                    _result = False
                logging.debug('[{}]: LED {} set to {}: {}'.format(_stage, chn, val, _result))
            if _result: self.alert = True
            Adaptor.publish_msg(
                'response',
                {'stage': 'success', 'status': 'success' if _result else 'failed'}
            )
            logging.debug('[{}] response: {}'.format(_stage, 'success' if _result else 'failed'))

    def set_gpio_status (self, chn, stat):
        ''' set single gpio status '''
        if DEBUG:
            _stat = 0 if stat == 'low' else 1
            FAKE_STAT[chn] = _stat
        else:
            _stat = GPIO.LOW if stat == 'low' else GPIO.HIGH
            GPIO.output(CHN[chn], _stat)

    def get_gpio_status (self, chn):
        ''' get {chn} IO status'''
        if DEBUG:
            return FAKE_STAT[chn]
        else:
            return GPIO.input(CHN[chn])

    def get_gpios_status (self):
        ''' get all IO status'''
        _dict = {}
        for chn in CHN.keys():
            _dict[chn] = 'on' if self.get_gpio_status(chn) == 1 else 'off'
        return _dict

    def _servo_change (self):
        ''' change server stage when alert occured '''
        if DEBUG:
            logging.debug('Simulate servo rotation for alert accured')
        else:
            self.servo_th = threading.Thread(target=self.__alert_servo)
            self.servo_th.start()   

    def __alert_servo (self):
        ''' thread for servo process when alert occured '''
        a2d = lambda a : 100 - (2.5 + (12.0 - 2.5)/180*(a+90))

        _pwm = GPIO.PWM(ALERT_OUT['pwm'], 50)
        for d in [a2d(0), a2d(90), a2d(0)]:
            _pwm.start(d)
            time.sleep(2)
        _pwm.stop()

    def get_status (self):
        ''' update adaptor status'''
        r = Adaptor.get_status(self)
        r.update(self.get_gpios_status())
        return r
    
    def get_info(self):
        ''' get adaptor information '''
        return Adaptor.get_info(self)

    def mod_close(self):
        ''' close the module '''
        if not DEBUG:
            GPIO.cleanup()
        self.th_switch_quit.set()

if __name__ == '__main__':
    import argsutils as au
    from adaptor import add_common_adaptor_args

    parser = au.init_parser('Raspberry Pi Tester Controller')
    add_common_adaptor_args(
        parser, 
        id='vid1',
        type='type1',
        status_period=30,
    )
    args = au.parse_args(parser)

    rpiCtrl = RaspiController(args=args)
    rpiCtrl.start()
    try:
        while not rpiCtrl.is_quit(1):
            pass
    except KeyboardInterrupt:
        rpiCtrl.mod_close()