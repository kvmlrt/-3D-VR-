# -*- coding: utf-8 -*-
import sys
import cv2
import numpy as np
from PyQt5.QtWidgets import QApplication, QWidget, QLabel, QPushButton, QVBoxLayout, QHBoxLayout
from PyQt5.QtCore import QTimer
from PyQt5.QtGui import QImage, QPixmap
import pyqtgraph.opengl as gl
from skimage.measure import marching_cubes
from scipy.ndimage import binary_closing, binary_opening

face_names = ['front', 'back', 'left', 'right', 'top', 'bottom']

class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("六面体素重建优化Demo")
        self.resize(1100, 650)
        self.images = [None]*6
        self.current_face = 0

        # 左侧摄像头画面和按钮
        self.cam_label = QLabel()
        self.cam_label.setFixedSize(400, 300)
        self.btn_capture = QPushButton("拍摄 {}面".format(face_names[self.current_face]))
        self.btn_capture.clicked.connect(self.capture_face)
        self.btn_voxel = QPushButton("体素重建并展示")
        self.btn_voxel.setEnabled(False)
        self.btn_voxel.clicked.connect(self.voxel_reconstruct)

        vbox_left = QVBoxLayout()
        vbox_left.addWidget(self.cam_label)
        vbox_left.addWidget(self.btn_capture)
        vbox_left.addWidget(self.btn_voxel)
        vbox_left.addStretch(1)

        # 右侧3D网格展示区
        self.gl_widget = gl.GLViewWidget()
        self.gl_widget.setFixedSize(600, 600)
        self.gl_widget.setBackgroundColor('w')
        self.gl_widget.setCameraPosition(distance=3)
        self.mesh_item = None

        vbox_right = QVBoxLayout()
        vbox_right.addWidget(self.gl_widget)
        vbox_right.addStretch(1)

        hbox = QHBoxLayout()
        hbox.addLayout(vbox_left)
        hbox.addLayout(vbox_right)
        self.setLayout(hbox)

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
            pixmap = QPixmap.fromImage(qt_img).scaled(400, 300, aspectRatioMode=1)
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
        # 智能抠图：自动阈值+形态学+平滑
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        # OTSU自动阈值
        _, mask = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
        # 闭运算填补小孔
        kernel = np.ones((5,5), np.uint8)
        mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
        # 开运算去除小噪点
        mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
        # 边缘平滑
        mask = cv2.GaussianBlur(mask, (3,3), 0)
        return (mask > 127).astype(np.uint8)

    def voxel_reconstruct(self):
        N = 96  # 分辨率，越大越精细但越慢
        voxel = np.ones((N, N, N), dtype=bool)
        masks = []
        for img in self.images:
            img = cv2.resize(img, (N, N))
            mask = self.get_mask(img)
            masks.append(mask)
        for z in range(N):
            voxel[:, :, z] &= masks[0][:, z].astype(bool)
            voxel[:, :, z] &= masks[1][:, N-1-z].astype(bool)
        for x in range(N):
            voxel[x, :, :] &= masks[2][:, x].astype(bool)[:, None]
            voxel[x, :, :] &= masks[3][:, N-1-x].astype(bool)[:, None]
        for y in range(N):
            voxel[:, y, :] &= masks[4][y, :].astype(bool)
            voxel[:, y, :] &= masks[5][N-1-y, :].astype(bool)
        # 三维形态学平滑
        voxel = binary_closing(voxel, structure=np.ones((3,3,3)))
        voxel = binary_opening(voxel, structure=np.ones((3,3,3)))
        # marching cubes重建网格
        verts, faces, normals, values = marching_cubes(voxel, level=0.5, spacing=(1.0/N, 1.0/N, 1.0/N))
        verts = verts - 0.5  # 居中
        # 清除旧网格
        if self.mesh_item:
            self.gl_widget.removeItem(self.mesh_item)
        mesh = gl.GLMeshItem(vertexes=verts, faces=faces, faceColors=None, drawEdges=False, drawFaces=True, smooth=True, color=(0.2,0.2,0.8,1))
        self.gl_widget.addItem(mesh)
        self.mesh_item = mesh

if __name__ == '__main__':
    app = QApplication(sys.argv)
    win = MainWindow()
    win.show()
    sys.exit(app.exec_()) 