import requests
import os
import cv2
import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D

def get_largest_object_mask(gray, threshold=30):
    _, binary = cv2.threshold(gray, threshold, 255, cv2.THRESH_BINARY)
    num_labels, labels, stats, centroids = cv2.connectedComponentsWithStats(binary, connectivity=8)
    if num_labels <= 1:
        return np.zeros_like(gray, dtype=bool)
    largest_label = 1 + np.argmax(stats[1:, cv2.CC_STAT_AREA])
    mask = (labels == largest_label)
    return mask

# 只处理这些后缀的图片
ALLOWED_EXTS = {'.jpg', '.jpeg', '.png', '.bmp'}
def is_image_file(fname):
    return os.path.splitext(fname)[1].lower() in ALLOWED_EXTS

img_list_url = "http://127.0.0.1:5001/api/list"
img_base_url = "http://127.0.0.1:5001/api/download/"
download_dir = "downloaded_imgs"
os.makedirs(download_dir, exist_ok=True)

resp = requests.get(img_list_url)
try:
    img_files = [f for f in resp.json()["files"] if is_image_file(f)]
except Exception as e:
    print("接口返回内容：", resp.text)
    print("解析JSON失败，报错：", e)
    exit(1)

if not img_files:
    print("没有可下载的图片。")
    exit(1)

print("将下载以下图片：")
for fname in img_files:
    print(" -", fname)
ans = input("是否继续下载并生成点云？(y/n): ")
if ans.lower() != 'y':
    print("已取消。")
    exit(0)

local_files = []
for fname in img_files:
    url = img_base_url + fname
    local_path = os.path.join(download_dir, fname)
    with open(local_path, "wb") as f:
        f.write(requests.get(url).content)
    local_files.append(local_path)
print(f"已下载图片: {local_files}")

# 2. 生成点云并分批写入CSV
z_scale = 50.0
step = 18  # 采样步长调为18，点云稀疏度适中
points_list = []
for img_path in local_files:
    img = cv2.imread(img_path, cv2.IMREAD_UNCHANGED)
    if img is None: continue
    if len(img.shape) == 2:
        gray = img
        mask = np.ones_like(gray, dtype=bool)
    elif len(img.shape) == 3 and img.shape[2] == 3:
        b, g, r = cv2.split(img)
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        # 绿色像素点过滤：G通道比R、B都高且高出一定阈值
        mask = ~((g > r + 30) & (g > b + 30))
    elif len(img.shape) == 3 and img.shape[2] == 4:
        b, g, r, a = cv2.split(img)
        gray = cv2.cvtColor(img, cv2.COLOR_BGRA2GRAY)
        mask = ~((g > r + 30) & (g > b + 30))
    else:
        continue
    # 只保留中心物体
    object_mask = get_largest_object_mask(gray)
    mask = mask & object_mask
    for y in range(0, gray.shape[0], step):
        for x in range(0, gray.shape[1], step):
            if not mask[y, x]:
                continue
            y_flip = gray.shape[0] - 1 - y  # y轴翻转
            z = float(gray[y, x]) / 255.0 * z_scale
            points_list.append([x, y_flip, z])

points_arr = np.array(points_list)
if points_arr.shape[0] == 0:
    print("没有有效点云生成。"); exit(1)
# 居中归一化到[-100,100]
center = points_arr.mean(axis=0)
points_arr -= center
max_range = np.abs(points_arr).max()
if max_range > 0:
    points_arr /= max_range
    points_arr *= 100

with open('points.csv', 'w') as f:
    f.write('x,y,z\n')
    for x, y, z in points_arr:
        f.write(f"{x},{y},{z}\n")
print(f'点云已保存为 points.csv，总点数：{len(points_arr)}')

# 3. 生成后立即窗口展示点云（matplotlib 3D）
# 读取刚生成的点云
points = points_arr
fig = plt.figure(figsize=(8,8))
ax = fig.add_subplot(111, projection='3d')
sc = ax.scatter(points[:,0], points[:,1], points[:,2], s=2, c=points[:,2], cmap='viridis')
ax.set_xlabel('X')
ax.set_ylabel('Y')
ax.set_zlabel('Z')
ax.set_title('点云预览')
plt.tight_layout()
plt.savefig('pointcloud_preview.png', dpi=200)
plt.show()
print("点云展示图已保存为 pointcloud_preview.png") 