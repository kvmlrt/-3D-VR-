import sys
import cv2
import numpy as np
from PyQt5.QtWidgets import QApplication, QWidget, QLabel, QPushButton, QVBoxLayout, QHBoxLayout
from PyQt5.QtCore import QTimer, Qt
from PyQt5.QtGui import QImage, QPixmap
import open3d as o3d

face_names = ['front', 'back', 'left', 'right', 'top', 'bottom']

class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("六面体素重建Demo")
        self.resize(900, 500)
        self.images = [None]*6
        self.current_face = 0

        # 左侧摄像头画面
        self.cam_label = QLabel()
        self.cam_label.setFixedSize(400, 300)
        self.btn_capture = QPushButton("拍摄 {}面".format(face_names[self.current_face]))
        self.btn_capture.clicked.connect(self.capture_face)
        self.btn_voxel = QPushButton("体素重建并可视化")
        self.btn_voxel.setEnabled(False)
        self.btn_voxel.clicked.connect(self.voxel_reconstruct)

        # 布局
        vbox_left = QVBoxLayout()
        vbox_left.addWidget(self.cam_label)
        vbox_left.addWidget(self.btn_capture)
        vbox_left.addWidget(self.btn_voxel)
        vbox_left.addStretch(1)
        self.setLayout(vbox_left)

        # 摄像头定时器
        self.cap = cv2.VideoCapture(0)
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_frame)
        self.timer.start(30)

    def update_frame(self):
        ret, frame = self.cap.read()
        if ret:
            img_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            h, w, ch = img_rgb.shape
            qt_img = QImage(img_rgb.data, w, h, ch*w, QImage.Format_RGB888)
            pixmap = QPixmap.fromImage(qt_img).scaled(400, 300, Qt.KeepAspectRatio)
            self.cam_label.setPixmap(pixmap)
            self.current_frame = frame

    def capture_face(self):
        if hasattr(self, 'current_frame'):
            self.images[self.current_face] = self.current_frame.copy()
            self.current_face += 1
            if self.current_face < 6:
                self.btn_capture.setText("拍摄 {}面".format(face_names[self.current_face]))
            else:
                self.btn_capture.setEnabled(False)
                self.btn_voxel.setEnabled(True)

    def get_mask(self, img):
        # 简单阈值抠图，假设背景为白色
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        _, mask = cv2.threshold(gray, 220, 255, cv2.THRESH_BINARY_INV)
        return mask // 255  # 0/1

    def voxel_reconstruct(self):
        N = 128  # 分辨率
        voxel = np.ones((N, N, N), dtype=bool)
        # 预处理图片为N*N
        masks = []
        for img in self.images:
            img = cv2.resize(img, (N, N))
            mask = self.get_mask(img)
            masks.append(mask)
        # 前后
        for z in range(N):
            voxel[:, :, z] &= masks[0][:, z]
            voxel[:, :, z] &= masks[1][:, N-1-z]
        # 左右
        for x in range(N):
            voxel[x, :, :] &= masks[2][:, x][:, None]
            voxel[x, :, :] &= masks[3][:, N-1-x][:, None]
        # 上下
        for y in range(N):
            voxel[:, y, :] &= masks[4][y, :]
            voxel[:, y, :] &= masks[5][N-1-y, :]
        points = np.argwhere(voxel)
        points = points / N  # 归一化
        # 可视化
        pcd = o3d.geometry.PointCloud()
        pcd.points = o3d.utility.Vector3dVector(points)
        o3d.visualization.draw_geometries([pcd], window_name='体素重建点云')
        o3d.io.write_point_cloud('voxel_output.ply', pcd)
        print('点云已保存为 voxel_output.ply')

if __name__ == '__main__':
    app = QApplication(sys.argv)
    win = MainWindow()
    win.show()
    sys.exit(app.exec_()) 