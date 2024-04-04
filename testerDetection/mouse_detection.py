import cv2
import numpy as np

imageCollection = ['neg_1.jpg', 'neg_2.jpg', 'neg_3.jpg', 'neg_4.jpg', 'neg_5.jpg',
                   'neg_6.jpg', 'neg_8.jpg', 'neg_9.jpg', 'neg_10.jpg',
                   'pos_1.jpg', 'pos_2.jpg', 'pos_3.jpg', 'pos_4.jpg', 'pos_5.jpg',
                   'pos_6.jpg', 'pos_7.jpg', 'pos_8.jpg', 'pos_9.jpg', 'pos_10.jpg',
                   'pos_11.jpg', 'pos_12.jpg', 'pos_13.jpg', 'pos_14.jpg', 'pos_15.jpg']

imageCollectionBonus = ['t2_1.jpg', 't2_2.jpg', 't2_3.jpg', 't2_4.jpg', 't2_5.jpg', 't2_6.jpg']

threshold = 0.7
videoPath = '/Users/juneyoungseo/Documents/Panasonic/test_videos/2023-12-26 10-36-47-ex2 SDU CT Tester.mp4'
FOLDER_PATH_BONUS = 'input/bonus/'
dDepth = cv2.CV_8U
method = cv2.TM_CCORR_NORMED
thresholdUpper = 255.0
thresholdLower = 23
templatePath = '/Users/juneyoungseo/PycharmProjects/pythonProject1/Mouse-Cursor-Detection/input/template.png'


def GetEdgesfromImage(imageName):
    imageName = cv2.GaussianBlur(imageName, (3, 3), 0)
    imageName = cv2.Laplacian(imageName, dDepth)
    ret, imageName = cv2.threshold(imageName, thresholdLower, thresholdUpper, cv2.THRESH_BINARY)
    imageName = cv2.GaussianBlur(imageName, (3, 3), 0)
    return imageName

def processVideo(videoPath, templatePath):
    cap = cv2.VideoCapture(videoPath)
    originalTemplate = cv2.imread(templatePath, 0)
    originalTemplate = GetEdgesfromImage(originalTemplate)

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        frameGray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        frameGray = GetEdgesfromImage(frameGray)

        scales = [(1, 1), (0.95, 0.95), (0.9, 0.9), (0.85, 0.85), (0.8, 0.8), (0.75, 0.75),
                  (0.7, 0.7), (0.65, 0.65), (0.6, 0.6), (0.55, 0.55), (0.5, 0.5)]  # Adjust scale range and step as needed

        detected = False
        for scale in scales:
            templateResized = cv2.resize(originalTemplate, (0,0), fx=scale[0], fy=scale[1])
            w, h = templateResized.shape[::-1]
            matchLevel = cv2.matchTemplate(frameGray, templateResized, method)
            loc = np.where(matchLevel >= threshold)

            for pt in zip(*loc[::-1]):
                cv2.rectangle(frame, pt, (pt[0] + w, pt[1] + h), (0, 255, 0), 2)
                detected = True

            if detected:
                print("Cursor detected.")
                break  # Remove this if you want to detect at all scales

        cv2.imshow('frame', frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):  # Press 'q' to exit
            break

    cap.release()
    cv2.destroyAllWindows()

# Call the function with your video and template paths
processVideo(videoPath, templatePath)

# def video_image(filename):
#     cap = cv2.VideoCapture(filename)
#
#     return cap
#
#
#
#     # imagePath = str(FOLDER_PATH + testImage)
# cap = video_image(FOLDER_PATH)
#
# while True:
#     ret, frame = cap.read()
#     if not ret:
#         break
#
#     for testImage in imageCollection:
#         # imagePath = video_image(frame)
#         origianlImage = frame
#
#
#         origianlImageGrayScale = cv2.cvtColor(origianlImage, cv2.COLOR_BGR2GRAY)
#         origianlImageGrayScale = GetEdgesfromImage(origianlImageGrayScale)
#
#         originalTemplate = cv2.imread(templateName, 0)
#         originalTemplate = GetEdgesfromImage(originalTemplate)
#
#         origianlImageGrayScaleCopy = origianlImageGrayScale.copy()
#
#         scales = [(1, 1), (0.95, 0.95), (0.9, 0.9), (0.85, 0.85), (0.8, 0.8), (0.75, 0.75),
#                   (0.7, 0.7), (0.65, 0.65), (0.6, 0.6), (0.55, 0.55), (0.5, 0.5)]
#
#         for scale in (scales):
#             templateResize = cv2.resize(originalTemplate, (0, 0), fx=scale[0], fy=scale[1])
#             h, w = templateResize.shape
#             origianlImageGrayScale = origianlImageGrayScaleCopy.copy()
#
#             matchLevel = cv2.matchTemplate(origianlImageGrayScale, templateResize, method)
#
#             loc = np.where(matchLevel >= threshold)
#             origianlImageForDrawing = origianlImage.copy()
#             detected = 0
#             for pt in zip(*loc[::-1]):
#                 detected += 1
#                 cv2.rectangle(origianlImageForDrawing, pt, (pt[0] + w, pt[1] + h), (0, 255, 0), 2)
#             if detected:
#                 cv2.imshow(testImage, origianlImageForDrawing)
#                 cv2.waitKey(0)
#                # cv2.imwrite(FOLDER_PATH + "detected_" + testImage, origianlImageForDrawing)
#                 print("Cursor found in " + testImage)
#                 break
#             cv2.destroyAllWindows()
#         if (detected == 0):
#             print("No cursor found in " + testImage)
#
# # cap.release(0)
# cv2.destroyAllWindows()