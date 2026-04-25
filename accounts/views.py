import os
import joblib
import pandas as pd
from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm
from django.conf import settings


from .models import BurnoutRecord  

ML_DIR = os.path.join(settings.BASE_DIR, 'ml_assets')

try:
    MODEL = joblib.load(os.path.join(ML_DIR, 'burnout_model_v3.pkl'))
    SCALER = joblib.load(os.path.join(ML_DIR, 'scaler_v3.pkl'))
    FEATURES = joblib.load(os.path.join(ML_DIR, 'features_v3.pkl'))
except Exception as e:
    print(f"Error loading ML assets: {e}")
    MODEL, SCALER, FEATURES = None, None, None



def register_view(request):
    if request.method == "POST":
        form = UserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('login')
    else:
        form = UserCreationForm()
    return render(request, 'accounts/register.html', {'form': form})

def login_view(request):
    if request.method == "POST":
        u = request.POST.get('username')
        p = request.POST.get('password')
        user = authenticate(request, username=u, password=p)
        if user is not None:
            login(request, user)
            return redirect('dashboard')
        else:
            messages.error(request, "Invalid username or password.")
    return render(request, "accounts/login.html")

def predict_burnout(request):
    if request.method == 'POST':
        current_sleep = float(request.POST.get('sleep_hours'))
        
        previous_record = BurnoutData.objects.filter(user=request.user).order_by('-created_at').first()
        
        message = ""
        if previous_record:
            diff = current_sleep - previous_record.sleep_hours
            if diff > 0:
                message = f"Incredible! You slept {diff} hours more than last time. You're recovering!"
            elif diff == 0 and current_sleep >= 8:
                message = "Consistency is power! You're maintaining peak rest levels."
            else:
                message = "Keep pushing for that extra hour of rest tonight!"

        new_record = BurnoutData.objects.create(user=request.user, sleep_hours=current_sleep)
        return render(request, 'dashboard.html', {'motivation': message})
from .models import BurnoutRecord

def your_predict_view(request):
    if request.method == "POST":
       
        current_sleep = float(request.POST.get('sleep_hours', 0))
        previous_record = BurnoutRecord.objects.filter(user=request.user).order_by('-created_at').first()
        
        motivation = ""
        sleep_diff = 0      
        if previous_record:
            sleep_diff = current_sleep - previous_record.sleep_hours
            if sleep_diff > 0:
                motivation = f"Great work! You're sleeping {sleep_diff} hours more than your last check-in. Your body is recovering!"
            elif sleep_diff == 0 and current_sleep >= 7:
                motivation = "Consistent rest is key! You are maintaining a healthy sleep schedule."
            else:
                motivation = "Small steps matter. Let's try to get a bit more rest tonight."

        context = {
            'motivation': motivation,
            'current_sleep': current_sleep,
            'sleep_diff': round(sleep_diff, 1),
            'sleep_percentage': min((current_sleep / 8) * 100, 100),
        }
        return render(request, 'dashboard.html', context)
from .models import BurnoutRecord  # Make sure this is imported

def logout_view(request):
    logout(request)
    return redirect('login')



@login_required(login_url='login')
def dashboard_view(request):
    risk_result = None
    color_class = "" 
    pros = [] 
    cons = [] 
    
    # --- PROGRESS TRACKING VARIABLES ---
    motivation = ""
    sleep_diff = 0
    current_sleep = 0
    sleep_percentage = 0

    if request.method == 'POST':
        
        
        try:
            # 1. Extract Form Data
            age = float(request.POST.get('age', 20))
            gender_str = request.POST.get('gender')
            gender = 1 if gender_str == 'male' else 0
            cgpa = float(request.POST.get('cgpa', 7.0))
            attendance = float(request.POST.get('attendance', 75))
            study_hrs = float(request.POST.get('study_hours', 0))
            sleep_hrs = float(request.POST.get('sleep_hours', 0))
            pressure_str = request.POST.get('academic_pressure') # Fixed name to match your HTML
            pressure = 5 if pressure_str == 'yes' else 1
            anxiety_str = request.POST.get('anxiety')
            anxiety = 5 if anxiety_str == 'yes' else 1

            # 2. CALC PROGRESS BEFORE SAVING NEW RECORD
            current_sleep = sleep_hrs
            previous_record = BurnoutRecord.objects.filter(user=request.user).order_by('-created_at').first()
            
            if previous_record and previous_record.sleep_hours:
                sleep_diff = current_sleep - previous_record.sleep_hours
                if sleep_diff > 0:
                    motivation = f"Great work! You're sleeping {round(sleep_diff, 1)} hours more than last time."
                elif sleep_diff < 0:
                    motivation = f"You slept {round(abs(sleep_diff), 1)} hours less than last time. Watch out!"
                else:
                    motivation = "Consistent sleep patterns detected!"
            else:
                motivation = "First assessment complete! Keep tracking to see your progress."

            sleep_percentage = min((current_sleep / 8) * 100, 100)

            # 3. ML PREDICTION LOGIC
            input_dict = {
                'age': age, 'gender': gender, 'course': 1, 'year': 3,
                'daily_study_hours': study_hrs, 'daily_sleep_hours': sleep_hrs,
                'screen_time_hours': 5.0, 'stress_level': pressure,
                'anxiety_score': anxiety, 'depression_score': 1,
                'academic_pressure_score': pressure, 'financial_stress_score': 2,
                'social_support_score': 3, 'physical_activity_hours': 1.0,
                'sleep_quality': 3, 'attendance_percentage': attendance,
                'cgpa': cgpa, 'internet_quality': 3
            }

            df = pd.DataFrame([input_dict])
            df = df[FEATURES]

            if MODEL and SCALER:
                scaled_data = SCALER.transform(df)
                prediction = MODEL.predict(scaled_data)[0]

                if prediction == 2:
                    risk_result, color_class = "High", "high-risk"
                elif prediction == 1:
                    risk_result, color_class = "Moderate", "mod-risk"
                else:
                    risk_result, color_class = "Low", "low-risk"
                

                
                # 5. GENERATE PROS/CONS
                pros = []
                cons = []
                if sleep_hrs >= 7.5:
                    pros.append("<strong>🛌 Excellent Sleep Hygiene:</strong> Your current sleep duration is a massive shield.")
                elif sleep_hrs < 6.5:
                    cons.append("<strong>🛌 Sleep Deprivation:</strong> Current sleep patterns are critically low.")
                strengths_text = "\n".join(pros) if pros else "No specific strengths noted."
                risks_text = "\n".join(cons) if cons else "No major risk factors noted."

# 3. NOW SAVE EVERYTHING
            BurnoutRecord.objects.create(
               user=request.user,
               risk_score=float(prediction),
               status=risk_result,
               sleep_hours=sleep_hrs,
               strengths=strengths_text,
               risk_factors=risks_text
        )
            if 4.0 >= study_hrs <= 6.0:
                    pros.append("<strong>📚 Balanced Study Routine:</strong> You've found the 'Sweet Spot'.")
            elif study_hrs > 9.0:
                    cons.append("<strong>📚 Hyper-Focus Risk:</strong> Studying over 9 hours elevates stress.")
                

            else:
                messages.error(request, "Analytical Engine assets are currently unavailable.")

        except Exception as e:
            pressure_str = request.POST.get('academic_pressure')

    # --- FINAL CONTEXT: MUST INCLUDE ALL PROGRESS DATA ---
    # Change the return at the bottom of dashboard_view to this:
    return render(request, 'accounts/dashboard.html', {
    'risk_result': risk_result, 
    'color_class': color_class,
    'pros': pros,
    'cons': cons,
    'motivation': motivation,
    'current_sleep': current_sleep if current_sleep > 0 else None, # Force show
    'sleep_diff': round(sleep_diff, 1),
    'sleep_percentage': sleep_percentage
})
   

@login_required(login_url='login')
def history_view(request):
    """View to display the user's past burnout predictions."""
    user_history = BurnoutRecord.objects.filter(user=request.user).order_by('-date_created')
    
    return render(request, 'accounts/history.html', {
        'history': user_history
    })  

def logout_view(request):
    logout(request)
    return redirect('login')
