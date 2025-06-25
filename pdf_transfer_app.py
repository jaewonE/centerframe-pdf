import sys
import os
import threading
import subprocess
from pathlib import Path
from typing import List

# PyQt6.QtWidgets에서 필요한 클래스들을 더 명시적으로 가져옵니다.
from PyQt6 import QtCore, QtGui, QtWidgets
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QIcon, QPaintEvent, QKeyEvent, QDragEnterEvent, QDropEvent
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QGroupBox, QLineEdit, QPushButton, QListWidget, QProgressBar,
    QMessageBox, QFileDialog, QListWidgetItem, QLabel, QStyle, QStatusBar
)

# 아래 라인을 통해 실제 PDF 변환 함수를 가져옵니다.
# 이 파일이 실제로 존재해야 합니다.
from center_pdf import center_pdf


class ConversionWorker(QtCore.QThread):
    """PDF 변환 작업을 수행하는 워커 스레드"""
    progress_update = pyqtSignal(int, int, str)
    finished = pyqtSignal(int, int)
    # is_cancelled 플래그를 추가하여 취소 시 특별한 처리를 할 수 있도록 합니다.
    is_cancelled = False

    def __init__(self, file_paths: List[str], output_dir: str):
        super().__init__()
        self.file_paths = file_paths
        self.output_dir = output_dir
        self.is_running = True

    def run(self):
        total_count = len(self.file_paths)
        success_count = 0
        failure_count = 0

        for i, file_path in enumerate(self.file_paths):
            if not self.is_running:
                # 외부에서 중단 신호를 받으면 is_cancelled 플래그를 설정하고 루프를 빠져나갑니다.
                self.is_cancelled = True
                break

            base_name = os.path.basename(file_path)
            output_file_path = os.path.join(self.output_dir, base_name)
            self.progress_update.emit(i + 1, total_count, base_name)

            try:
                is_success = center_pdf(file_path, output_file_path)
                if is_success:
                    success_count += 1
                else:
                    failure_count += 1
            except Exception as e:
                print(f"Error converting {base_name}: {e}")
                failure_count += 1

        self.finished.emit(success_count, failure_count)

    def stop(self):
        self.is_running = False


class DragDropListWidget(QListWidget):
    """드래그 앤 드롭을 지원하고, 안내 메시지를 표시하는 리스트 위젯"""
    # ↓ 메인윈도우에 파일 경로를 알리는 커스텀 시그널
    fileDropped = QtCore.pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAcceptDrops(True)
        self.setSelectionMode(
            QtWidgets.QAbstractItemView.SelectionMode.NoSelection)
        self.setDropIndicatorShown(True)

        # ── MainWindow가 시그널을 받을 수 있게 자동 연결
        main_win = self.window()
        if hasattr(main_win, "add_file_item"):
            self.fileDropped.connect(main_win.add_file_item)

    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            for url in event.mimeData().urls():
                if url.toLocalFile().lower().endswith('.pdf'):
                    event.acceptProposedAction()
                    return
        event.ignore()

    def dragMoveEvent(self, event: QtGui.QDragMoveEvent):
        event.acceptProposedAction()

    def dropEvent(self, event: QDropEvent):
        # 커스텀 시그널을 통해 메인윈도우에 전달
        for url in event.mimeData().urls():
            file_path = url.toLocalFile()
            if file_path.lower().endswith(".pdf"):
                self.fileDropped.emit(file_path)

        event.acceptProposedAction()      # 드롭 최종 수락
        self.viewport().update()

    def paintEvent(self, event: QPaintEvent):
        super().paintEvent(event)
        if self.count() == 0:
            painter = QtGui.QPainter(self.viewport())
            painter.save()
            font = self.font()
            font.setPointSize(12)
            painter.setFont(font)
            color = self.palette().color(QtGui.QPalette.ColorRole.Mid)
            painter.setPen(color)
            rect = self.viewport().rect()
            painter.drawText(
                rect, Qt.AlignmentFlag.AlignCenter, "PDF 파일을 이곳으로 드래그하거나\n'파일 추가' 버튼으로 선택해주세요.")
            painter.restore()

# (개선) MainWindow 클래스에 모든 로직을 통합하고 UI 개선 사항을 적용


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("PDF 레터박스 중앙 정렬")
        self.resize(800, 650)

        # (제안 8) 애플리케이션 아이콘 설정
        # QStyle을 사용하여 운영체제 기본 아이콘을 가져올 수 있습니다.
        # app_icon = self.style().standardIcon(QStyle.StandardPixmap.SP_FileIcon)
        # self.setWindowIcon(app_icon)
        # 또는 특정 이미지 파일 사용: self.setWindowIcon(QIcon("path/to/icon.png"))

        self.settings = QtCore.QSettings("MyCompany", "PDFCenteringApp")
        self.conversion_worker = None

        self.init_ui()
        self.apply_stylesheet()

        # (제안 1) 앱 시작 시 저장 경로 유효성 검사
        self.validate_saved_path()

    def init_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(15, 15, 15, 15)
        main_layout.setSpacing(10)

        # 1. 저장 경로 선택 영역
        path_group = QGroupBox("1. 변환된 파일을 저장할 경로")
        path_layout = QHBoxLayout()
        self.path_edit = QLineEdit(
            self, placeholderText="저장될 폴더 경로를 선택하세요.", readOnly=True)
        path_button = QPushButton("폴더 선택", self)
        path_button.clicked.connect(self.select_output_dir)
        path_layout.addWidget(self.path_edit)
        path_layout.addWidget(path_button)
        path_group.setLayout(path_layout)
        main_layout.addWidget(path_group)

        # 2. 파일 목록 영역
        list_group = QGroupBox("2. 변환할 PDF 파일 목록")
        list_layout = QVBoxLayout()
        self.file_list_widget = DragDropListWidget(self)
        list_layout.addWidget(self.file_list_widget, 1)

        # (제안 3, 4) 파일 추가 및 목록 비우기 버튼
        list_button_layout = QHBoxLayout()
        list_button_layout.addStretch(1)
        self.add_files_button = QPushButton(self.style().standardIcon(
            QStyle.StandardPixmap.SP_FileIcon), " 파일 추가...")
        self.add_files_button.clicked.connect(self.add_files_dialog)
        self.clear_list_button = QPushButton(self.style().standardIcon(
            QStyle.StandardPixmap.SP_TrashIcon), " 목록 비우기")
        self.clear_list_button.clicked.connect(self.clear_file_list)
        list_button_layout.addWidget(self.add_files_button)
        list_button_layout.addWidget(self.clear_list_button)
        list_layout.addLayout(list_button_layout)
        list_group.setLayout(list_layout)
        main_layout.addWidget(list_group, 1)

        # 3. 변환 실행 및 진행률 표시 영역
        action_group = QGroupBox("3. 변환 실행")
        action_layout = QVBoxLayout()
        self.progress_bar = QProgressBar(
            self, value=0, textVisible=True, format="%p%")

        # (제안 7) 변환/취소 버튼
        self.convert_cancel_button = QPushButton("변환 시작", self)
        self.convert_cancel_button.setMinimumHeight(40)
        self.convert_cancel_button.setObjectName("ConvertButton")
        self.convert_cancel_button.clicked.connect(self.toggle_conversion)
        action_layout.addWidget(self.progress_bar)
        action_layout.addWidget(self.convert_cancel_button)
        action_group.setLayout(action_layout)
        main_layout.addWidget(action_group)

        # (제안 6) 상태 표시줄 추가
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("준비")

    # (제안 5) 스타일시트 적용
    def apply_stylesheet(self):
        self.setStyleSheet("""
            QMainWindow, QWidget {
                background-color: #f0f0f0;
            }
            QGroupBox {
                font-size: 14px;
                font-weight: bold;
                border: 1px solid #ccc;
                border-radius: 8px;
                margin-top: 10px;
                background-color: #fafafa;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                subcontrol-position: top left;
                padding: 0 5px;
                left: 10px;
            }
            QPushButton {
                background-color: #0078d7;
                color: white;
                border: none;
                padding: 8px 16px;
                font-size: 13px;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #005a9e;
            }
            QPushButton:disabled {
                background-color: #a0a0a0;
            }
            #ConvertButton {
                font-size: 16px;
                font-weight: bold;
            }
            #ConvertButton:hover {
                background-color: #005a9e;
            }
            QLineEdit {
                padding: 5px;
                border: 1px solid #ccc;
                border-radius: 5px;
                background-color: #fff;
            }
            QListWidget {
                border: 2px dashed #aaa;
                border-radius: 8px;
                background-color: #fdfdfd;
            }
            QProgressBar {
                border: 1px solid #ccc;
                border-radius: 5px;
                text-align: center;
                font-size: 12px;
                color: #333;
            }
            QProgressBar::chunk {
                background-color: #0078d7;
                border-radius: 4px;
            }
            QStatusBar {
                font-size: 12px;
            }
        """)

    # (제안 1) 저장 경로 유효성 검사 메서드
    def validate_saved_path(self):
        saved_path = self.settings.value("outputDir", "")
        if saved_path and not os.path.isdir(saved_path):
            QMessageBox.warning(
                self, "경고",
                f"이전에 저장된 경로를 찾을 수 없습니다:\n{saved_path}\n\n"
                "새로운 저장 경로를 선택해주세요."
            )
            self.path_edit.clear()
        elif saved_path:
            self.path_edit.setText(saved_path)
        else:
            self.path_edit.setText(str(Path.home()))

    # (제안 2) 파일 아이템을 리스트에 추가하는 메서드 (삭제 버튼 포함)

    def add_file_item(self, file_path):
        current_paths = [self.file_list_widget.itemWidget(self.file_list_widget.item(
            i)).findChild(QLabel).text() for i in range(self.file_list_widget.count())]
        if file_path in current_paths:
            return

        item = QListWidgetItem(self.file_list_widget)
        item_widget = QWidget()
        item_layout = QHBoxLayout(item_widget)
        item_layout.setContentsMargins(5, 5, 5, 5)

        file_label = QLabel(file_path)
        file_label.setToolTip(file_path)  # 긴 경로를 위해 툴팁 추가

        delete_button = QPushButton(self.style().standardIcon(
            QStyle.StandardPixmap.SP_TrashIcon), "")
        delete_button.setFixedSize(24, 24)
        delete_button.setStyleSheet(
            "background-color: #e81123; border-radius: 12px;")

        # lambda 함수로 현재 아이템을 캡처하여 삭제 로직 연결
        delete_button.clicked.connect(
            lambda _, it=item: self.file_list_widget.takeItem(self.file_list_widget.row(it)))

        item_layout.addWidget(file_label)
        item_layout.addStretch()
        item_layout.addWidget(delete_button)

        item.setSizeHint(item_widget.sizeHint())
        self.file_list_widget.addItem(item)
        self.file_list_widget.setItemWidget(item, item_widget)

    def select_output_dir(self):
        current_path = self.path_edit.text() or str(Path.home())
        directory = QFileDialog.getExistingDirectory(
            self, "저장할 폴더를 선택하세요", current_path)
        if directory:
            self.path_edit.setText(directory)
            self.settings.setValue("outputDir", directory)

    # (제안 4) '파일 추가' 대화상자
    def add_files_dialog(self):
        files, _ = QFileDialog.getOpenFileNames(
            self, "PDF 파일 선택", "", "PDF Files (*.pdf)")
        for file_path in files:
            self.add_file_item(file_path)

    # (제안 3) '목록 비우기' 메서드
    def clear_file_list(self):
        self.file_list_widget.clear()

    # (제안 7) 변환 시작/취소 토글 메서드
    def toggle_conversion(self):
        if self.conversion_worker and self.conversion_worker.isRunning():
            # 변환 중이면 취소 로직 실행
            reply = QMessageBox.question(self, "변환 취소", "진행 중인 변환 작업을 취소하시겠습니까?",
                                         QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
            if reply == QMessageBox.StandardButton.Yes:
                self.conversion_worker.stop()
                self.set_ui_enabled(False)  # UI는 계속 비활성화 상태 유지
                self.convert_cancel_button.setText("취소 중...")
                self.status_bar.showMessage("변환 취소 중...")
        else:
            # 변환 시작 로직 실행
            self.start_conversion()

    def start_conversion(self):
        output_dir = self.path_edit.text()
        if not output_dir or not os.path.isdir(output_dir):
            QMessageBox.warning(self, "경고", "유효한 저장 경로를 선택해주세요.")
            return

        if self.file_list_widget.count() == 0:
            QMessageBox.warning(self, "경고", "변환할 PDF 파일을 추가해주세요.")
            return

        file_paths = [self.file_list_widget.itemWidget(self.file_list_widget.item(
            i)).findChild(QLabel).text() for i in range(self.file_list_widget.count())]

        self.set_ui_enabled(False)
        self.progress_bar.setRange(0, len(file_paths))
        self.progress_bar.setValue(0)
        self.status_bar.showMessage("변환 준비 중...")

        self.conversion_worker = ConversionWorker(file_paths, output_dir)
        self.conversion_worker.progress_update.connect(self.update_progress)
        self.conversion_worker.finished.connect(self.on_conversion_finished)
        self.conversion_worker.start()

    def update_progress(self, current, total, filename):
        self.progress_bar.setValue(current)
        self.status_bar.showMessage(f"({current}/{total}) {filename} 변환 중...")

    def on_conversion_finished(self, success_count, failure_count):
        self.set_ui_enabled(True)
        total_count = success_count + failure_count

        if self.conversion_worker and self.conversion_worker.is_cancelled:
            self.status_bar.showMessage(
                f"사용자에 의해 변환이 취소되었습니다. (성공: {success_count}, 실패: {failure_count})")
            QMessageBox.information(self, "작업 취소", "변환 작업이 사용자에 의해 취소되었습니다.")
            return

        self.status_bar.showMessage(
            f"변환 완료! (성공: {success_count}, 실패: {failure_count})")

        msg_box = QMessageBox(self)
        open_folder_button = None

        if failure_count == 0 and success_count > 0:
            msg_box.setIcon(QMessageBox.Icon.Information)
            msg_box.setWindowTitle("변환 완료")
            msg_box.setText(f"총 {total_count}개의 파일이 모두 성공적으로 변환되었습니다.")
            open_folder_button = msg_box.addButton(
                "폴더 열기", QMessageBox.ButtonRole.ActionRole)
            msg_box.addButton("확인", QMessageBox.ButtonRole.AcceptRole)
            # (제안 3) 성공 시 목록 자동 비우기
            self.clear_file_list()
        elif success_count == 0 and failure_count > 0:
            msg_box.setIcon(QMessageBox.Icon.Critical)
            msg_box.setWindowTitle("변환 실패")
            msg_box.setText(
                f"총 {total_count}개의 파일 모두 변환에 실패했습니다.\n터미널/콘솔 로그에서 오류를 확인해주세요.")
            msg_box.addButton("확인", QMessageBox.ButtonRole.AcceptRole)
        else:  # 일부 성공, 일부 실패
            msg_box.setIcon(QMessageBox.Icon.Warning)
            msg_box.setWindowTitle("일부 파일 변환 실패")
            msg_box.setText(
                f"총 {total_count}개의 파일 중 {success_count}개 변환 성공, {failure_count}개 실패했습니다.")
            open_folder_button = msg_box.addButton(
                "폴더 열기", QMessageBox.ButtonRole.ActionRole)
            msg_box.addButton("확인", QMessageBox.ButtonRole.AcceptRole)

        msg_box.exec()

        if open_folder_button and msg_box.clickedButton() == open_folder_button:
            self.open_output_directory()

    def open_output_directory(self):
        output_dir = self.path_edit.text()
        if os.path.isdir(output_dir):
            try:
                if sys.platform == "win32":
                    os.startfile(output_dir)
                elif sys.platform == "darwin":
                    subprocess.run(["open", output_dir], check=False)
                else:
                    subprocess.run(["xdg-open", output_dir], check=False)
            except Exception as e:
                QMessageBox.warning(self, "오류", f"폴더를 여는 데 실패했습니다: {e}")

    def set_ui_enabled(self, enabled: bool):
        # 모든 그룹박스를 찾아 활성화/비활성화
        for group_box in self.findChildren(QGroupBox):
            group_box.setEnabled(enabled)

        # 개별 버튼 상태 제어
        self.add_files_button.setEnabled(enabled)
        self.clear_list_button.setEnabled(enabled)

        if enabled:
            self.convert_cancel_button.setText("변환 시작")
            self.convert_cancel_button.setEnabled(True)
            self.convert_cancel_button.setStyleSheet(
                "#ConvertButton { background-color: #0078d7; }")
        else:
            self.convert_cancel_button.setText("취소")
            self.convert_cancel_button.setEnabled(True)  # 취소를 위해 활성화 유지
            self.convert_cancel_button.setStyleSheet(
                "#ConvertButton { background-color: #d13438; }")

    def closeEvent(self, event: QtGui.QCloseEvent):
        # 창을 닫기 전 설정 저장 및 실행 중인 스레드 정리
        self.settings.setValue("outputDir", self.path_edit.text())
        if self.conversion_worker and self.conversion_worker.isRunning():
            self.conversion_worker.stop()
            self.conversion_worker.wait()  # 스레드가 완전히 종료될 때까지 대기
        super().closeEvent(event)


def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == '__main__':
    main()
