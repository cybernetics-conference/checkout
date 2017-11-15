import pygame
import pygame.font
import pygame.camera
from PIL import Image
from pyzbar.pyzbar import decode
from pygame.locals import KEYDOWN, K_q
from datetime import datetime, timedelta
from db import DB
import requests
import socket

FULLSCREEN = True
LOCAL = False

# seconds before a book can be re-checked out
RECENT = 15

# seconds to show system messages
DISPLAY_LENGTH = 5

# layout
PADDING_X = 20
PADDING_Y = 20

# keep local record of checkouts and times
db = DB('checkouts')

# interface setup
dim = (800,600)
font_color = (255,255,255)
pygame.font.init()
font = pygame.font.SysFont('monospace', 32, bold=True)

# webcam setup
pygame.camera.init()
cams = pygame.camera.list_cameras()
cam = pygame.camera.Camera(cams[-1], dim)
cam.start()
cam_dim = cam.get_size()


def scan():
    img = cam.get_image()
    img = pygame.image.tostring(img, 'RGBA', False)
    try:
        img = Image.frombytes('RGBA', cam_dim, img)
        result = decode(img)
        return [r.data.decode('utf8') for r in result]
    except ValueError as e:
        return []


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


def wrap_text(text, width):
    lines = [[]]
    for word in text.split():
        if font.size(' '.join(lines[-1] + [word]))[0] < width - PADDING_X*2:
            lines[-1].append(word)
        else:
            lines.append(['  ', word])
    return [' '.join(line) for line in lines]


def remote_checkouts(q):
    while True:
        url, attendee_id = child.recv()
        resp = requests.post(url, json={
            'attendee_id': attendee_id,
            'station_id': socket.gethostname()
        })
        book = resp.json()
        child.send({'url': url, 'book': book})


if __name__ == '__main__':
    # raspberry pi 3 has some wifi hardware latency issues
    # where requests take up to 5sec for a response.
    # so throw them to a separate process so
    # they don't block the webcam
    from multiprocessing import Process, Pipe
    parent, child = Pipe()
    request_proc = Process(target=remote_checkouts, args=(child,))
    request_proc.start()

    # map urls -> titles for visual feedback
    to_display = ('', datetime.now())

    pygame.init()
    if FULLSCREEN:
        display = pygame.display.set_mode(dim, pygame.FULLSCREEN)
    else:
        display = pygame.display.set_mode(dim, 0)

    capture = True
    was_scanned = False
    while capture:
        # check the checkout process
        # for new results
        if parent.poll():
            data = parent.recv()
            # not being used atm

        # show info on display
        y = PADDING_Y
        line_spacing = 2
        img = cam.get_image()
        img = pygame.transform.scale(img, dim)
        elapsed = (datetime.now() - to_display[1]).seconds
        if elapsed < DISPLAY_LENGTH:
            lines = wrap_text(to_display[0], img.get_width())
            for line in lines:
                label = font.render(line, 0, font_color, (0,0,0))
                label.set_alpha((1-elapsed/DISPLAY_LENGTH) * 255)
                img.blit(label, (PADDING_X, y))
                y += font.size(line)[1] + line_spacing

        # flash color indicating successful scan
        if was_scanned:
            pygame.draw.rect(img, (0,0,255), (0,0,dim[0],dim[1]), 0)
            was_scanned = False

        display.blit(img, (0,0))
        pygame.display.flip()

        # q to quit
        for event in pygame.event.get():
            if event.type == KEYDOWN and event.key == K_q:
                capture = False

        # scan and filter results
        scanned = scan()
        attendee_id, urls = None, []
        for s in scanned:
            # attendee QR codes have 'planet' in their url
            if 'planet' in s:
                attendee_id = s.replace('http://library.cybernetics.social/planet/', '')
            elif recently_scanned(s):
                continue
            else:
                urls.append(s)

        if attendee_id is None and urls:
            to_display = ('Please scan your QR code with the book', datetime.now())
            continue

        for url in urls:
            # track local checkouts
            db.append({
                'ts': datetime.now().timestamp(),
                'url': url
            })

            # no https on server
            url = url.replace('https', 'http')
            if LOCAL:
                url = url.replace('library.cybernetics.social', 'localhost:5000')
            was_scanned = True

            # send url to checkout process to deal with
            parent.send((url, attendee_id))

            # give some visual feedback about the checkout
            to_display = ('Thank you', datetime.now())

    request_proc.terminate()
    request_proc.join()
    cam.stop()
    pygame.quit()
