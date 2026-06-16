"""Редактор кейса целиком для текущего среза: мета + этап «Пациенты» (Constructor).

Без визуальной полировки: только функциональные виджеты и layout-менеджеры. Публичные поля
меты, список редакторов пациентов и кнопки — точки доступа для тестов. Сборка в домен —
через ``to_draft`` (далее ``build_case`` из слоя приложения).
"""
from __future__ import annotations

import uuid

from PySide6.QtWidgets import (
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLineEdit,
    QPushButton,
    QScrollArea,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from educase_constructor.ui.clinical_editor import ClinicalEditor
from educase_constructor.ui.contacts_editor import ContactsEditor
from educase_constructor.ui.environment_editor import EnvironmentEditor
from educase_constructor.ui.final_editor import FinalEditor
from educase_constructor.ui.icons import load_icon
from educase_constructor.ui.list_helpers import make_placeholder, refresh_placeholder, wrap_in_card
from educase_constructor.ui.patient_editor import PatientEditor
from educase_constructor.ui.ses_editor import SesEditor
from educase_core.application.case_builder import CaseDraft


class CaseEditor(QWidget):
    """Редактор меты кейса и всех шести этапов прохождения."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)

        # Служебный id кейса преподавателем не вводится: генерируется один раз и стабилен в
        # пределах сессии редактирования (повторное «Сохранить» даёт тот же id).
        self._case_id = uuid.uuid4().hex

        self.title_edit = QLineEdit(self)
        self.author_edit = QLineEdit(self)
        self.nosology_edit = QLineEdit(self)
        self.unit_personnel_edit = QLineEdit(self)

        self.patient_editors: list[PatientEditor] = []
        self._patient_cards: list[QGroupBox] = []

        meta_form = QFormLayout()
        meta_form.addRow("Название", self.title_edit)
        meta_form.addRow("Автор", self.author_edit)
        meta_form.addRow("Нозология", self.nosology_edit)
        meta_form.addRow("Личный состав", self.unit_personnel_edit)

        self.add_patient_button = QPushButton("Добавить", self)
        self.add_patient_button.setIcon(load_icon("add"))
        self.remove_patient_button = QPushButton("Удалить", self)
        self.remove_patient_button.setIcon(load_icon("delete"))
        self.add_patient_button.clicked.connect(self.add_patient)
        self.remove_patient_button.clicked.connect(self.remove_last_patient)

        patient_buttons = QHBoxLayout()
        patient_buttons.addWidget(self.add_patient_button)
        patient_buttons.addWidget(self.remove_patient_button)
        patient_buttons.addStretch(1)

        self._empty_label = make_placeholder("Пока не добавлено ни одного пациента")

        self._patients_layout = QVBoxLayout()

        patients_box = QGroupBox("Пациенты")
        patients_box_layout = QVBoxLayout(patients_box)
        patients_box_layout.addLayout(patient_buttons)
        patients_box_layout.addWidget(self._empty_label)
        patients_box_layout.addLayout(self._patients_layout)

        self.clinical_editor = ClinicalEditor(self)
        self.contacts_editor = ContactsEditor(self)
        self.environment_editor = EnvironmentEditor(self)
        self.ses_editor = SesEditor(self)
        self.final_editor = FinalEditor(self)

        # Вкладка «Кейс и пациенты»: мета-форма + блок пациентов.
        case_tab = QWidget()
        case_tab_layout = QVBoxLayout(case_tab)
        case_tab_layout.addLayout(meta_form)
        case_tab_layout.addWidget(patients_box)

        self.tabs = QTabWidget(self)
        self.tabs.addTab(self._scroll_tab(case_tab), "Кейс и пациенты")
        self.tabs.addTab(self._scroll_tab(self.clinical_editor), "Клинический")
        self.tabs.addTab(self._scroll_tab(self.contacts_editor), "Контакты")
        self.tabs.addTab(self._scroll_tab(self.environment_editor), "Среда")
        self.tabs.addTab(self._scroll_tab(self.ses_editor), "СЭС")
        self.tabs.addTab(self._scroll_tab(self.final_editor), "Финал")
        self.tabs.setTabIcon(0, load_icon("stage_patients"))
        self.tabs.setTabIcon(1, load_icon("stage_clinical"))
        self.tabs.setTabIcon(2, load_icon("stage_contacts"))
        self.tabs.setTabIcon(3, load_icon("stage_environment"))
        self.tabs.setTabIcon(4, load_icon("stage_ses"))
        self.tabs.setTabIcon(5, load_icon("stage_final"))

        layout = QVBoxLayout(self)
        layout.addWidget(self.tabs)

        self._refresh_empty()

    def _scroll_tab(self, content: QWidget) -> QScrollArea:
        """Обернуть содержимое вкладки в прокручиваемую область, прибитую к верху.

        Контент кладётся в контейнер с растяжкой снизу, поэтому редакторы этапов
        получают естественную высоту, а секции не расползаются вертикальными дырами.
        ``setWidgetResizable(True)`` растягивает контейнер по ширине области и даёт
        вертикальную прокрутку высоким редакторам вместо их сжатия.
        """
        container = QWidget()
        container_layout = QVBoxLayout(container)
        container_layout.addWidget(content)
        container_layout.addStretch(1)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(container)
        return scroll

    def add_patient(self) -> None:
        """Добавить редактор нового пациента в конец списка."""
        editor = PatientEditor(self)
        self.patient_editors.append(editor)
        card = wrap_in_card(editor, f"Пациент {len(self.patient_editors)}")
        self._patient_cards.append(card)
        self._patients_layout.addWidget(card)
        self._refresh_empty()

    def remove_last_patient(self) -> None:
        """Удалить последний редактор пациента (если он есть)."""
        if not self.patient_editors:
            return
        self.patient_editors.pop()
        card = self._patient_cards.pop()
        self._patients_layout.removeWidget(card)
        card.deleteLater()
        self._refresh_empty()

    def _refresh_empty(self) -> None:
        """Обновить видимость подсказки пустого состояния списка пациентов."""
        refresh_placeholder(self._empty_label, is_empty=len(self.patient_editors) == 0)

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
            case_id=self._case_id,
            title=self.title_edit.text(),
            author=self.author_edit.text(),
            nosology=self.nosology_edit.text(),
            unit_personnel=self._unit_personnel(),
            patients=tuple(editor.to_draft() for editor in self.patient_editors),
            clinical=self.clinical_editor.to_draft(),
            contacts=self.contacts_editor.to_draft(),
            environment=self.environment_editor.to_draft(),
            ses=self.ses_editor.to_draft(),
            final=self.final_editor.to_draft(),
        )
