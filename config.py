# -*- coding: utf-8 -*-
"""
Created on Sat Jun 21 04:21:54 2025

@author: Kenneth Okeke
@emial: okekekenchi0802@gmail.com

This file contains configuration settings for the application.
"""

# --- Application Settings ---

APP_NAME = "CDS Data Validation Tool"
APP_VERSION = "1.0.0"
DEBUG_MODE = True

# --- Session Settings ---
SESSION_LIFETIME = 120 #minutes

# --- Database Settings ---

DATABASE_URL = ""
DATABASE_NAME = "cds.db"

# Router
ROUTE_LOGIN = "pages/1_login.py"
ROUTE_REGISTER = "pages/2_register.py"
ROUTE_HOME = "pages/3_home.py"
