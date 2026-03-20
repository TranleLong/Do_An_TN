import subprocess
print("Makemigrations:")
print(subprocess.getoutput("python manage.py makemigrations"))
print("Migrate:")
print(subprocess.getoutput("python manage.py migrate"))
print("Seed:")
print(subprocess.getoutput("python seed_data.py"))
