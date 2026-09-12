"""开发启动入口；生产使用 gunicorn 'app_factory:create_app()'。"""
import os
from app_factory import create_app

if __name__ == '__main__':
    os.environ.setdefault('APP_ENV', 'development')
    create_app().run(host='127.0.0.1', port=int(os.environ.get('PORT', '6173')), debug=False)
