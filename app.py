#%%
from ultralytics import YOLO,checks
import cv2 as cv
# import PIL.Image as Image
# import PIL.ImageColor as ImageColor
# import PIL.ImageDraw as ImageDraw
# import PIL.ImageFont as ImageFont

# from IPython.display import display
import os
import yaml
import time


import pygame
import numpy as np

print(f'opencv version {cv.__version__}')
checks()


#%% read config file yaml
# Read config file yaml
config_file_path = 'config.yaml'
sample_config_file_path = 'sample.config.yaml'

# Check if config.yaml exists, if not create one from sample.config.yaml
if not os.path.exists(config_file_path):
    if os.path.exists(sample_config_file_path):
        with open(sample_config_file_path, 'r') as sample_f:
            sample_config = sample_f.read()
        with open(config_file_path, 'w') as new_f:
            new_f.write(sample_config)
        print(f"{config_file_path} created from {sample_config_file_path}")
    else:
        print(f"{sample_config_file_path} does not exist. Cannot create {config_file_path}")
else:
    print(f"{config_file_path} already exists.")

# Read the actual config file
with open(config_file_path) as f:
    config = yaml.load(f, Loader=yaml.FullLoader)
print(config)



# %%
try :
    model = YOLO(config['WEIGHT'])  # load a pretrained YOLOv8n detection model
    
    print(f'model loaded success : {config["WEIGHT"]}')
    print('model names : ',model.names)
    # Load class names
    class_names = model.names
    
except Exception as e:
    print(e)
    print('model load failed')
    quit()

#%%
cap = cv.VideoCapture(0)
print(f'width: {cap.get(cv.CAP_PROP_FRAME_WIDTH)} , height: {cap.get(cv.CAP_PROP_FRAME_HEIGHT)}')

#%%
# 원하는 해상도를 설정합니다.
#3840 x 2160  2mp
desired_width = config['CAM_WIDTH']
desired_height = config['CAM_HEIGHT']
# cap.set(cv.CAP_PROP_FRAME_WIDTH, desired_width)
# cap.set(cv.CAP_PROP_FRAME_HEIGHT, desired_height)

# 웹캠이 설정한 해상도를 지원하는지 확인합니다.
actual_width = cap.get(cv.CAP_PROP_FRAME_WIDTH)
actual_height = cap.get(cv.CAP_PROP_FRAME_HEIGHT)
if actual_width == desired_width and actual_height == desired_height:
    print(f"The webcam supports the resolution {desired_width}x{desired_height}")
else:
    print(f"The webcam does not support the resolution {desired_width}x{desired_height}")
    print(f"Available resolution is {actual_width}x{actual_height}")
    
#%% Pygame 초기화
pygame.init()
# 화면 설정
screen_width, screen_height = int(config['SCREEN_WIDTH']), int(config['SCREEN_HEIGHT'])
# screen = pygame.display.set_mode((desired_width, desired_height), pygame.FULLSCREEN)
screen = pygame.display.set_mode((screen_width, screen_height))

background = np.zeros((screen_width,screen_height, 3), dtype=np.uint8)

# Loop through the video frames
while cap.isOpened():
    
    # Pygame 이벤트 처리 (종료 등)
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            cap.release()
            cv.destroyAllWindows()
            quit()
    
    # Read a frame from the video
    success, frame = cap.read()
    if success:
         # Flip the frame horizontally
        frame = cv.flip(frame, 1)
        
        # Resize and position adjustment
        height, width, _ = frame.shape
        
        # Calculate the scale factor
        scale_x = screen_width / width
        scale_y = screen_height / height
        
        # Reset the background to black for the next frame
        background = cv.resize(frame, (screen_width, screen_height))
        
        
        # Use YOLO model to detect objects in the frame
        results = model(source=frame, conf=0.5, verbose=False)
        
        # Iterate through the results to get the bounding boxes
        for result in results:
            boxes = result.boxes
            for box in boxes:
                x1, y1, x2, y2 = box.xyxy[0]
                x1, y1, x2, y2 = int(x1 * scale_x), int(y1 * scale_y), int(x2 * scale_x), int(y2 * scale_y)
                cv.rectangle(background, (x1, y1), (x2, y2), (0, 255, 0), 2)
                
                # Get class and confidence
                class_id = int(box.cls.cpu().item())
                class_name = class_names[class_id]
                conf = int(box.conf.cpu().item() * 100)
                
                # Display class name and confidence
                label_text = f"{class_name} {conf}%"
                cv.putText(background, label_text, (x1, y1 - 10), cv.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)
        
        
        # OpenCV 이미지를 Pygame 이미지로 변환
        frame_rgb = cv.cvtColor(background, cv.COLOR_BGR2RGB)
        frame_pygame = pygame.surfarray.make_surface(frame_rgb.swapaxes(0, 1))
        
        # 화면에 그리기
        screen.blit(frame_pygame, (0, 0))
        pygame.display.update()
        
        # esc 'q' 키를 누르면 종료
        keys = pygame.key.get_pressed()
        if keys[pygame.K_ESCAPE] or keys[pygame.K_q]:
            pygame.quit()
            cap.release()
            cv.destroyAllWindows()
            quit()

#%%
# Release the video capture object and close the display window
cap.release()
cv.destroyAllWindows()
# %%
