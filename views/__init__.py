"""
KALASAG - Views Package
Presentation layer containing Tkinter UI components.
"""

from views.theme import KalasagTheme
from views.components import (
    SearchableListbox,
    DataTable,
    SearchFrame,
    CardWidget,
    DashboardCard,
    ActionButton,
    StatusBadge,
    ConfirmDialog,
    StatusBar,
    FormDialog,
)
from views.main_app import MainApplication, run_application
from views.login_view import LoginView
from views.dashboard_view import DashboardView
from views.resident_view import ResidentView
from views.blotter_view import BlotterView
from views.document_view import DocumentView
from views.analytics_view import AnalyticsView
from views.admin_view import AdminView

__all__ = [
    'KalasagTheme',
    'SearchableListbox',
    'DataTable',
    'SearchFrame',
    'CardWidget',
    'DashboardCard',
    'ActionButton',
    'StatusBadge',
    'ConfirmDialog',
    'StatusBar',
    'FormDialog',
    'MainApplication',
    'run_application',
    'LoginView',
    'DashboardView',
    'ResidentView',
    'BlotterView',
    'DocumentView',
    'AnalyticsView',
    'AdminView',
]
