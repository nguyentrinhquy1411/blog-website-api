from fastapi.middleware.cors import CORSMiddleware


def setup_cors(app):
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # Điều chỉnh theo môi trường
        allow_methods=["*"],
        allow_headers=["*"],
    )