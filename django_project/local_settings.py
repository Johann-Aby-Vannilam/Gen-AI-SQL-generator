# Database
# https://docs.djangoproject.com/en/2.1/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'postgres',  # Replace with your database name
        'USER': 'postgres',   # Replace with your PostgreSQL username
        'PASSWORD': 'mannoor123',  
        'HOST': 'localhost',
        'PORT': '5432',
    }
}
MONGODB_SETTINGS = {
    "HOST": "localhost:27017",  # Replace with your MongoDB URI
    "DATABASE_NAME": "Project",  # Replace with your actual database name
}