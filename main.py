import pygame
import pygame.font
import pygame.camera
from PIL import Image
from pyzbar.pyzbar import decode
from pygame.locals import KEYDOWN, K_q
from datetime import datetime, timedelta
from db import DB
import requests

RECENT = 45 # seconds
db = DB('checkouts')
dim = (640,480)
pygame.font.init()
font = pygame.font.SysFont('monospace', 32, bold=True)
font_color = (255,255,0)
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


def recently_scanned(url):
    """check if the URL was recently scanned
    (to prevent double-scanning)"""
    recent = datetime.now() - timedelta(seconds=RECENT)
    for checkout in reversed(list(db.all())):
        dt = datetime.fromtimestamp(checkout['ts'])
        if dt < recent:
            break
        if checkout['url'] == url:
            return True
    return False

def remote_checkouts(q):
    while True:
        url = child.recv()
        resp = requests.post(url)
        book = resp.json()
        child.send(book)


if __name__ == '__main__':
    from multiprocessing import Process, Pipe

    parent, child = Pipe()
    request_proc = Process(target=remote_checkouts, args=(child,))
    request_proc.start()
    to_display = []
    pygame.init()
    display = pygame.display.set_mode(dim, 0)
    capture = True
    while capture:
        if parent.poll():
            book = parent.recv()
            to_display.append(book['title'])

        # show info on display
        x, y = 20, 20
        line_spacing = 2
        img = cam.get_image()
        for line in reversed(to_display):
            label = font.render(line, 0, font_color)
            img.blit(label, (x, y))
            y += font.size(line)[1] + line_spacing
        display.blit(img, (0,0))
        pygame.display.flip()

        # q to quit
        for event in pygame.event.get():
            if event.type == KEYDOWN and event.key == K_q:
                capture = False

        for url in scan():
            if recently_scanned(url):
                continue

            # track local checkouts
            db.append({
                'ts': datetime.now().timestamp(),
                'url': url
            })

            # no https on server
            url = url.replace('https', 'http')
            parent.send(url)
    cam.stop()
    pygame.quit()
    request_proc.join()