lệnh run server:
 - fastapi dev main.py --reload
 - uvicorn main:app --reload
 docker-compose up --build

Cách build:
    # Xóa images để build lại từ đầu
    docker-compose down --rmi all

    # Build lại images với --no-cache để đảm bảo cập nhật dependencies
    docker-compose build --no-cache

    # Khởi động lại containers
    docker-compose up -d

    docker logs -f blog_api

    docker-compose exec api alembic upgrade head
Lệnh test:
    docker-compose exec api pytest -v

Tạo môi trường ảo
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
deactive