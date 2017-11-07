import pygame
import pygame.font
import pygame.camera
from PIL import Image
from pyzbar.pyzbar import decode
from pygame.locals import KEYDOWN, K_s, K_q

dim = (1280,720)
pygame.font.init()
font = pygame.font.SysFont('monospace', 15)
pygame.camera.init()
cams = pygame.camera.list_cameras()
cam = pygame.camera.Camera(cams[-1], dim)
cam.start()


def scan():
    img = cam.get_image()
    img = pygame.image.tostring(img, 'RGBA', False)
    img = Image.frombytes('RGBA', dim, img)
    result = decode(img)
    return [r.data.decode('utf8') for r in result]


def scanner():
    """Runs a webcam scanner.
    Press q to quit, s to scan"""
    pygame.init()
    display = pygame.display.set_mode(dim, 0)
    last_results = []
    capture = True
    while capture:
        img = cam.get_image()
        label = font.render(
            ','.join(last_results),
            1, (255,255,0))
        img.blit(label, (100, 100))
        display.blit(img, (0,0))
        pygame.display.flip()
        for event in pygame.event.get():
            if event.type == KEYDOWN:
                if event.key == K_s:
                    last_results = scan()
                    yield last_results
                elif event.key == K_q:
                    capture = False
    cam.stop()
    pygame.quit()


if __name__ == '__main__':
    # q to quit
    # s to scan
    import requests
    for urls in scanner():
        for url in urls:
            requests.post(url)