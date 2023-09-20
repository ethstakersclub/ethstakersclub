"""
Django settings for ethstakersclub project.

Generated by 'django-admin startproject' using Django 4.2.1.

For more information on this file, see
https://docs.djangoproject.com/en/4.2/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/4.2/ref/settings/
"""


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/4.2/howto/deployment/checklist/

# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.sites',
    'django_celery_beat',
    'pwa',
    'allauth',
    'allauth.account',
    'allauth.socialaccount',
    'captcha',
    'blockfetcher',
    'api',
    'users',
    'frontend',
]

SITE_ID=1

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'ethstakersclub.urls'

WSGI_APPLICATION = 'ethstakersclub.wsgi.application'

AUTHENTICATION_BACKENDS = [
    'django.contrib.auth.backends.ModelBackend',
    'allauth.account.auth_backends.AuthenticationBackend',
]

ACCOUNT_FORMS = {
    'signup': 'users.forms.CustomSignupForm',
}

ACCOUNT_AUTHENTICATION_METHOD = 'email'
ACCOUNT_EMAIL_REQUIRED = True
ACCOUNT_USERNAME_REQUIRED = False
ACCOUNT_USER_MODEL_USERNAME_FIELD = None
ACCOUNT_EMAIL_VERIFICATION = 'none'

# Password validation
# https://docs.djangoproject.com/en/4.2/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

AUTH_USER_MODEL = 'users.CustomUser'


# Internationalization
# https://docs.djangoproject.com/en/4.2/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_TZ = True

LOGIN_REDIRECT_URL = 'dashboard_empty'
LOGOUT_REDIRECT_URL = 'dashboard_empty'

# Default primary key field type
# https://docs.djangoproject.com/en/4.2/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

ACTIVE_STATUSES = frozenset({"active_ongoing", "active_exiting", "active_slashed"})
PENDING_STATUSES = frozenset({"pending_queued", "pending_initialized"})
EXITED_STATUSES = frozenset({"exited_unslashed", "exited_slashed", "withdrawal_possible", "withdrawal_done"})
EXITING_STATUSES = frozenset({"active_exiting", "active_slashed"})

eth_clients = [
    {
        "client_name": "Nethermind",
        "repository_owner": "NethermindEth",
        "repo_name": "nethermind",
        "type": "execution"
    },
    {
        "client_name": "Geth",
        "repository_owner": "ethereum",
        "repo_name": "go-ethereum",
        "type": "execution"
    },
    {
        "client_name": "Erigon",
        "repository_owner": "ledgerwatch",
        "repo_name": "erigon",
        "type": "execution"
    },
    {
        "client_name": "Besu",
        "repository_owner": "hyperledger",
        "repo_name": "besu",
        "type": "execution"
    },
    {
        "client_name": "Teku",
        "repository_owner": "ConsenSys",
        "repo_name": "teku",
        "type": "consensus"
    },
    {
        "client_name": "Prysm",
        "repository_owner": "prysmaticlabs",
        "repo_name": "prysm",
        "type": "consensus"
    },
    {
        "client_name": "Nimbus",
        "repository_owner": "status-im",
        "repo_name": "nimbus-eth2",
        "type": "consensus"
    },
    {
        "client_name": "Lodestar",
        "repository_owner": "ChainSafe",
        "repo_name": "lodestar",
        "type": "consensus"
    },
    {
        "client_name": "Lighthouse",
        "repository_owner": "sigp",
        "repo_name": "lighthouse",
        "type": "consensus"
    },
    {
        "client_name": "MEV-Boost",
        "repository_owner": "flashbots",
        "repo_name": "mev-boost",
        "type": "other"
    }
]

# PWA

PWA_APP_ICONS = [
    {
        'src': '/static/img/favicon/android-icon-192x192.png',
        'sizes': '192x192'
    },
    {
        'src': '/static/img/favicon/android-icon-144x144.png',
        'sizes': '144x144'
    },
    {
        'src': '/static/img/favicon/android-icon-96x96.png',
        'sizes': '96x96'
    },
    {
        'src': '/static/img/favicon/android-icon-72x72.png',
        'sizes': '72x72'
    },
    {
        'src': '/static/img/favicon/android-icon-48x48.png',
        'sizes': '48x48'
    },
    {
        'src': '/static/img/favicon/android-icon-36x36.png',
        'sizes': '36x36'
    },
]
PWA_APP_ICONS_APPLE = [
    {
        'src': '/static/img/favicon/apple-icon-180x180.png',
        'sizes': '180x180'
    },
    {
        'src': '/static/img/favicon/apple-icon-152x152.png',
        'sizes': '152x152'
    },
    {
        'src': '/static/img/favicon/apple-icon-144x144.png',
        'sizes': '144x144'
    },
    {
        'src': '/static/img/favicon/apple-icon-120x120.png',
        'sizes': '120x120'
    },
    {
        'src': '/static/img/favicon/apple-icon-114x114.png',
        'sizes': '114x114'
    },
    {
        'src': '/static/img/favicon/apple-icon-76x76.png',
        'sizes': '76x76'
    },
    {
        'src': '/static/img/favicon/apple-icon-72x72.png',
        'sizes': '72x72'
    },
    {
        'src': '/static/img/favicon/apple-icon-60x60.png',
        'sizes': '60x60'
    },
    {
        'src': '/static/img/favicon/apple-icon-57x57.png',
        'sizes': '57x57'
    },
]
PWA_APP_SPLASH_SCREEN = [
    {
        'src': '/static/img/splash_screens/4__iPhone_SE__iPod_touch_5th_generation_and_later_landscape.png',
        'media': '(device-width: 320px) and (device-height: 568px) and (-webkit-device-pixel-ratio: 2)'
    },
    {
        'src': '/static/img/splash_screens/4__iPhone_SE__iPod_touch_5th_generation_and_later_portrait.png',
        'media': '(device-width: 320px) and (device-height: 568px) and (-webkit-device-pixel-ratio: 2)'
    },
    {
        'src': '/static/img/splash_screens/8.3__iPad_Mini_landscape.png',
        'media': '(device-width: 768px) and (device-height: 1024px) and (-webkit-device-pixel-ratio: 2)'
    },
    {
        'src': '/static/img/splash_screens/8.3__iPad_Mini_portrait.png',
        'media': '(device-width: 768px) and (device-height: 1024px) and (-webkit-device-pixel-ratio: 2)'
    },
    {
        'src': '/static/img/splash_screens/9.7__iPad_Pro__7.9__iPad_mini__9.7__iPad_Air__9.7__iPad_landscape.png',
        'media': '(device-width: 768px) and (device-height: 1024px) and (-webkit-device-pixel-ratio: 2)'
    },
    {
        'src': '/static/img/splash_screens/9.7__iPad_Pro__7.9__iPad_mini__9.7__iPad_Air__9.7__iPad_portrait.png',
        'media': '(device-width: 768px) and (device-height: 1024px) and (-webkit-device-pixel-ratio: 2)'
    },
    {
        'src': '/static/img/splash_screens/10.2__iPad_landscape.png',
        'media': '(device-width: 810px) and (device-height: 1080px) and (-webkit-device-pixel-ratio: 2)'
    },
    {
        'src': '/static/img/splash_screens/10.2__iPad_portrait.png',
        'media': '(device-width: 810px) and (device-height: 1080px) and (-webkit-device-pixel-ratio: 2)'
    },
    {
        'src': '/static/img/splash_screens/10.5__iPad_Air_landscape.png',
        'media': '(device-width: 834px) and (device-height: 1112px) and (-webkit-device-pixel-ratio: 2)'
    },
    {
        'src': '/static/img/splash_screens/10.5__iPad_Air_portrait.png',
        'media': '(device-width: 834px) and (device-height: 1112px) and (-webkit-device-pixel-ratio: 2)'
    },
    {
        'src': '/static/img/splash_screens/10.9__iPad_Air_landscape.png',
        'media': '(device-width: 810px) and (device-height: 1080px) and (-webkit-device-pixel-ratio: 2)'
    },
    {
        'src': '/static/img/splash_screens/10.9__iPad_Air_portrait.png',
        'media': '(device-width: 810px) and (device-height: 1080px) and (-webkit-device-pixel-ratio: 2)'
    },
    {
        'src': '/static/img/splash_screens/11__iPad_Pro__10.5__iPad_Pro_landscape.png',
        'media': '(device-width: 834px) and (device-height: 1194px) and (-webkit-device-pixel-ratio: 2)'
    },
    {
        'src': '/static/img/splash_screens/11__iPad_Pro__10.5__iPad_Pro_portrait.png',
        'media': '(device-width: 834px) and (device-height: 1194px) and (-webkit-device-pixel-ratio: 2)'
    },
    {
        'src': '/static/img/splash_screens/12.9__iPad_Pro_landscape.png',
        'media': '(device-width: 1024px) and (device-height: 1366px) and (-webkit-device-pixel-ratio: 2)'
    },
    {
        'src': '/static/img/splash_screens/12.9__iPad_Pro_portrait.png',
        'media': '(device-width: 1024px) and (device-height: 1366px) and (-webkit-device-pixel-ratio: 2)'
    },
    {
        'src': '/static/img/splash_screens/icon.png',
        'media': '(any-pointer: fine)'
    },
    {
        'src': '/static/img/splash_screens/iPhone_8__iPhone_7__iPhone_6s__iPhone_6__4.7__iPhone_SE_landscape.png',
        'media': '(device-width: 375px) and (device-height: 667px) and (-webkit-device-pixel-ratio: 2)'
    },
    {
        'src': '/static/img/splash_screens/iPhone_8__iPhone_7__iPhone_6s__iPhone_6__4.7__iPhone_SE_portrait.png',
        'media': '(device-width: 375px) and (device-height: 667px) and (-webkit-device-pixel-ratio: 2)'
    },
    {
        'src': '/static/img/splash_screens/iPhone_8_Plus__iPhone_7_Plus__iPhone_6s_Plus__iPhone_6_Plus_landscape.png',
        'media': '(device-width: 414px) and (device-height: 736px) and (-webkit-device-pixel-ratio: 3)'
    },
    {
        'src': '/static/img/splash_screens/iPhone_8_Plus__iPhone_7_Plus__iPhone_6s_Plus__iPhone_6_Plus_portrait.png',
        'media': '(device-width: 414px) and (device-height: 736px) and (-webkit-device-pixel-ratio: 3)'
    },
    {
        'src': '/static/img/splash_screens/iPhone_11__iPhone_XR_landscape.png',
        'media': '(device-width: 828px) and (device-height: 1792px) and (-webkit-device-pixel-ratio: 2)'
    },
    {
        'src': '/static/img/splash_screens/iPhone_11__iPhone_XR_portrait.png',
        'media': '(device-width: 828px) and (device-height: 1792px) and (-webkit-device-pixel-ratio: 2)'
    },
    {
        'src': '/static/img/splash_screens/iPhone_11_Pro_Max__iPhone_XS_Max_landscape.png',
        'media': '(device-width: 1242px) and (device-height: 2688px) and (-webkit-device-pixel-ratio: 3)'
    },
    {
        'src': '/static/img/splash_screens/iPhone_11_Pro_Max__iPhone_XS_Max_portrait.png',
        'media': '(device-width: 1242px) and (device-height: 2688px) and (-webkit-device-pixel-ratio: 3)'
    },
    {
        'src': '/static/img/splash_screens/iPhone_13_mini__iPhone_12_mini__iPhone_11_Pro__iPhone_XS__iPhone_X_landscape.png',
        'media': '(device-width: 1125px) and (device-height: 2436px) and (-webkit-device-pixel-ratio: 3)'
    },
    {
        'src': '/static/img/splash_screens/iPhone_13_mini__iPhone_12_mini__iPhone_11_Pro__iPhone_XS__iPhone_X_portrait.png',
        'media': '(device-width: 1125px) and (device-height: 2436px) and (-webkit-device-pixel-ratio: 3)'
    },
    {
        'src': '/static/img/splash_screens/iPhone_14__iPhone_13_Pro__iPhone_13__iPhone_12_Pro__iPhone_12_landscape.png',
        'media': '(device-width: 1170px) and (device-height: 2532px) and (-webkit-device-pixel-ratio: 3)'
    },
    {
        'src': '/static/img/splash_screens/iPhone_14__iPhone_13_Pro__iPhone_13__iPhone_12_Pro__iPhone_12_portrait.png',
        'media': '(device-width: 1170px) and (device-height: 2532px) and (-webkit-device-pixel-ratio: 3)'
    },
    {
        'src': '/static/img/splash_screens/iPhone_14_Plus__iPhone_13_Pro_Max__iPhone_12_Pro_Max_landscape.png',
        'media': '(device-width: 1284px) and (device-height: 2778px) and (-webkit-device-pixel-ratio: 3)'
    },
    {
        'src': '/static/img/splash_screens/iPhone_14_Plus__iPhone_13_Pro_Max__iPhone_12_Pro_Max_portrait.png',
        'media': '(device-width: 1284px) and (device-height: 2778px) and (-webkit-device-pixel-ratio: 3)'
    },
    {
        'src': '/static/img/splash_screens/iPhone_14_Pro_landscape.png',
        'media': '(device-width: 1284px) and (device-height: 2778px) and (-webkit-device-pixel-ratio: 3)'
    },
    {
        'src': '/static/img/splash_screens/iPhone_14_Pro_Max_landscape.png',
        'media': '(device-width: 1284px) and (device-height: 2778px) and (-webkit-device-pixel-ratio: 3)'
    },
    {
        'src': '/static/img/splash_screens/iPhone_14_Pro_Max_portrait.png',
        'media': '(device-width: 1284px) and (device-height: 2778px) and (-webkit-device-pixel-ratio: 3)'
    },
    {
        'src': '/static/img/splash_screens/iPhone_14_Pro_portrait.png',
        'media': '(device-width: 1284px) and (device-height: 2778px) and (-webkit-device-pixel-ratio: 3)'
    }
]
PWA_APP_DIR = 'ltr'
PWA_APP_LANG = 'en-US'
'''
PWA_APP_SHORTCUTS = [
    {
        'name': 'Shortcut',
        'url': '/target',
        'description': 'Shortcut to a page in my application'
    }
]
PWA_APP_SCREENSHOTS = [
    {
      'src': '/static/images/icons/splash-750x1334.png',
      'sizes': '750x1334',
      "type": "image/png"
    }
]
'''

from settings import *
from ethstakersclub.monitoring_ranks import MONITORING_RANKS