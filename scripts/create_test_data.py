import os
import sys
import django

# Add the project root directory to Python path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'DS2_SOA.settings')
django.setup()

from crop_app.models import FarmProfile, FieldPlot
from django.contrib.auth.models import User

def create_test_plots():
    """Create test user, farm, and plots for simulator"""
    
    print("=" * 60)
    print("Creating Test Data for Crop Monitoring System")
    print("=" * 60)
    
    # Check if plots already exist
    existing_plots = FieldPlot.objects.count()
    if existing_plots > 0:
        print(f"\n✓ Plots already exist: {existing_plots}")
        print("\nExisting Plots:")
        for plot in FieldPlot.objects.all():
            print(f"  - Plot {plot.id}: {plot.crop_variety} (Farm: {plot.farm.owner.username})")
        return
    
    print("\nCreating test data...")
    
    # Create a test user
    user, created = User.objects.get_or_create(
        username='test_farmer',
        defaults={
            'email': 'farmer@test.com',
            'first_name': 'Test',
            'last_name': 'Farmer'
        }
    )
    
    if created:
        user.set_password('testpass123')
        user.save()
        print(f"✓ Created user: {user.username}")
    else:
        print(f"✓ Using existing user: {user.username}")
    
    # Create a farm
    farm = FarmProfile.objects.create(
        owner=user,
        location="Tunis, Tunisia",
        size=100.0,
        crop_type="Wheat"
    )
    print(f"✓ Created farm: {farm.crop_type} farm in {farm.location}")
    
    # Create 3 plots for training data
    for i in range(1, 4):
        plot = FieldPlot.objects.create(
            farm=farm,
            crop_variety=f"Wheat Variety {i}"
        )
        print(f"✓ Created Plot {plot.id}: {plot.crop_variety}")
    
    print("\n" + "=" * 60)
    print(f"✅ Setup complete! Created {FieldPlot.objects.count()} plots")
    print("=" * 60)
    print("\nNext steps:")
    print("  1. Keep Django server running: python manage.py runserver")
    print("  2. Run simulator: python simulator/sensor_generator.py")
    print("=" * 60)

if __name__ == '__main__':
    create_test_plots()