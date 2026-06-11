"""Редактор кейса целиком для текущего среза: мета + этап «Пациенты» (Constructor).

Без визуальной полировки: только функциональные виджеты и layout-менеджеры. Публичные поля
меты, список редакторов пациентов и кнопки — точки доступа для тестов. Сборка в домен —
через ``to_draft`` (далее ``build_case`` из слоя приложения).
"""
from __future__ import annotations

from PySide6.QtWidgets import (
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from educase_constructor.ui.clinical_editor import ClinicalEditor
from educase_constructor.ui.patient_editor import PatientEditor
from educase_core.application.case_builder import CaseDraft


class CaseEditor(QWidget):
    """Редактор меты кейса и этапа «Пациенты»."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)

        self.case_id_edit = QLineEdit(self)
        self.title_edit = QLineEdit(self)
        self.author_edit = QLineEdit(self)
        self.nosology_edit = QLineEdit(self)
        self.unit_personnel_edit = QLineEdit(self)

        self.patient_editors: list[PatientEditor] = []

        meta_form = QFormLayout()
        meta_form.addRow("Идентификатор кейса", self.case_id_edit)
        meta_form.addRow("Название", self.title_edit)
        meta_form.addRow("Автор", self.author_edit)
        meta_form.addRow("Нозология", self.nosology_edit)
        meta_form.addRow("Личный состав", self.unit_personnel_edit)

        self.add_patient_button = QPushButton("Добавить пациента", self)
        self.remove_patient_button = QPushButton("Удалить последнего", self)
        self.add_patient_button.clicked.connect(self.add_patient)
        self.remove_patient_button.clicked.connect(self.remove_last_patient)

        patient_buttons = QHBoxLayout()
        patient_buttons.addWidget(self.add_patient_button)
        patient_buttons.addWidget(self.remove_patient_button)

        self._patients_layout = QVBoxLayout()

        patients_box = QGroupBox("Пациенты")
        patients_box_layout = QVBoxLayout(patients_box)
        patients_box_layout.addLayout(patient_buttons)
        patients_box_layout.addLayout(self._patients_layout)

        self.clinical_editor = ClinicalEditor(self)
        clinical_box = QGroupBox("Клинико-эпидемиологический диагноз")
        clinical_box_layout = QVBoxLayout(clinical_box)
        clinical_box_layout.addWidget(self.clinical_editor)

        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("Кейс"))
        layout.addLayout(meta_form)
        layout.addWidget(patients_box)
        layout.addWidget(clinical_box)
        layout.addStretch(1)

    def add_patient(self) -> None:
        """Добавить редактор нового пациента в конец списка."""
        editor = PatientEditor(self)
        self.patient_editors.append(editor)
        self._patients_layout.addWidget(editor)

    def remove_last_patient(self) -> None:
        """Удалить последний редактор пациента (если он есть)."""
        if not self.patient_editors:
            return
        editor = self.patient_editors.pop()
        self._patients_layout.removeWidget(editor)
        editor.deleteLater()

    def _unit_personnel(self) -> int | None:
        text = self.unit_personnel_edit.text().strip()
        if not text:
            return None
        try:
            return int(text)
        except ValueError:
            return None

    def to_draft(self) -> CaseDraft:
        """Собрать ``CaseDraft`` из меты и всех редакторов пациентов."""
        return CaseDraft(
            case_id=self.case_id_edit.text(),
            title=self.title_edit.text(),
            author=self.author_edit.text(),
            nosology=self.nosology_edit.text(),
            unit_personnel=self._unit_personnel(),
            patients=tuple(editor.to_draft() for editor in self.patient_editors),
            clinical=self.clinical_editor.to_draft(),
        )
