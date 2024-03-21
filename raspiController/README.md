# Raspberry Pi Controller
Code containing below functions:

* establish Redis connection
* GPIO Plugin Module

### Operation
Run below command to start controller:

At Raspberry Pi, run below command to start adaptor code
```python
python3 adaptor/raspi-controller.py --redis-host [redis_server_IP] -d
```