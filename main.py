import pygetwindow as gw
import pyautogui
import time
import keyboard
import random
import os
import sys
import numpy as np
from collections import deque
from pynput.mouse import Button, Controller
from scipy.ndimage import label, center_of_mass, generate_binary_structure, sum as ndi_sum
from collections import defaultdict
from scipy.spatial import cKDTree

os.system('title telegram: Blum app clicker')

mouse = Controller()

window_input = "\nWindow name (1 - TelegramDesktop | 2 - iMe): "
window_not_found = "[❌] | Window - {} not found!"
window_found = "[✅] | Window found - {}\nPress 'q' for pause"
pause_message = "Pause \nPress 'q' again to continue"
continue_message = 'Continue...'

def find_island_centers(matrix, distance_buffer):
    matrix = np.array(matrix, dtype=bool)

    # Label connected components (islands)
    structure = np.ones((3, 3), dtype=bool)
    labeled_matrix, num_features = label(matrix, structure=structure)

    if num_features == 0:
        return []

    # Compute sum of x, y coordinates and counts for each feature
    y_indices, x_indices = np.nonzero(matrix)
    labels = labeled_matrix[y_indices, x_indices]

    sum_coords = np.zeros((num_features, 2), dtype=float)
    counts = np.zeros(num_features, dtype=int)

    for x, y, l in zip(x_indices, y_indices, labels):
        sum_coords[l-1] += [y, x]  # Use l-1 to avoid off-by-one indexing
        counts[l-1] += 1

    # Calculate centers of islands
    centers = sum_coords / counts[:, None]

    # Use cKDTree to find pairs within the distance buffer
    tree = cKDTree(centers)
    pairs = tree.query_pairs(distance_buffer)

    # Union-Find to merge clusters based on distance
    parent = np.arange(num_features)

    def find(p):
        if parent[p] != p:
            parent[p] = find(parent[p])
        return parent[p]

    def union(p, q):
        root_p = find(p)
        root_q = find(q)
        if root_p != root_q:
            parent[root_q] = root_p

    for i, j in pairs:
        union(i, j)

    # Merge centers by summing coordinates and recalculating centroids
    cluster_sum = np.zeros((num_features, 2), dtype=float)
    cluster_count = np.zeros(num_features, dtype=int)

    for i in range(num_features):
        root = find(i)
        cluster_sum[root] += centers[i] * counts[i]
        cluster_count[root] += counts[i]

    merged_centers = cluster_sum[cluster_count > 0] / cluster_count[cluster_count > 0][:, None]
    sorted_centers = merged_centers[np.argsort(merged_centers[:, 0])]

    return sorted_centers

def click(x, y):
    mouse.position = (x, y + random.randint(1, 3))
    mouse.press(Button.left)
    mouse.release(Button.left)

window_name = input(window_input)

if window_name == '1':
    window_name = "TelegramDesktop"

if window_name == '2':
    window_name = "iMe"

check = gw.getWindowsWithTitle(window_name)
if not check:
    print(window_not_found.format(window_name))
    sys.exit()
else:
    print(window_found.format(window_name))

telegram_window = check[0]

paused = False

while True:
    if keyboard.is_pressed('q'):
        paused = not paused
        if paused:
            print(pause_message)
        else:
            print(continue_message)
        time.sleep(0.2)

    if paused:
        continue

    window_rect = (
        telegram_window.left, telegram_window.top, telegram_window.width, telegram_window.height
    )

    if telegram_window != []:
        try:
            telegram_window.activate()
        except:
            telegram_window.minimize()
            telegram_window.restore()

    scrn = pyautogui.screenshot(region=(window_rect[0], window_rect[1], window_rect[2], window_rect[3]))
    start_time = time.perf_counter()
    width, height = scrn.size

    grid = np.zeros((height, width), dtype=int)

    for x in range(0, width):
        for y in range(140, height-45):
            r, g, b = scrn.getpixel((x, y))
            if (((r in range(30, 230)) and (g in range(170, 254)) and (b in range(0, 90))) and
                ((r not in range(130, 250)) and (g not in range(90, 210)) and (b not in range(45, 230)))):
                grid[y][x] = 1

    centers = find_island_centers(grid, distance_buffer=4)

    for x in centers:

        screen_x = window_rect[0] + float(x[1])
        screen_y = window_rect[1] + float(x[0])
        end_time = time.perf_counter()
        elapsed_time = (end_time - start_time) * 1000
        print(f"Elapsed time: {elapsed_time:.4f} seconds")
        if elapsed_time > 129:
            break
        screen_y_y = screen_y + (elapsed_time * 0.56)
        if screen_x >= window_rect[0] and screen_x <= window_rect[0] + width and screen_y_y >= window_rect[1] and screen_y_y <= window_rect[1] + height:
            click(screen_x, screen_y_y)
#             time.sleep(0.001)
