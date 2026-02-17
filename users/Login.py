from django import forms

class LoginForm(forms.Form):
    username = forms.CharField(max_length=200, label="Username or Email")
    password = forms.CharField(widget=forms.PasswordInput, label="Password")

    def clean(self):
        cleaned_data = super().clean()
        username = cleaned_data.get("username")
        password = cleaned_data.get("password")

        if username and password:
            return cleaned_data

        raise forms.ValidationError("ERROR: username & Password")

    


from django.views import View
from django.contrib.auth import authenticate, login
from django.shortcuts import render, redirect
from .forms import LoginForm
from auth0 import AuthManager

class LoginPage(View):
    """
    LoginPage handles the GET and POST requests for the login screen.
    It depends on an external AuthManager class to perform user validation.
    """
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.auth_manager = AuthManager()  

    def get(self, request):
        """
        Handles GET requests.
        Preconditions: The GET request contains no form data.
        Postconditions: Renders the login page.
        """
        form = LoginForm()
        return render(request, 'LoginPage.html',{"form": form})

    def post(self, request):
        """
        Handles POST requests to authenticate a user.
        Preconditions: Request.POST contains 'user' and 'password' fields.
        Postconditions:
          - If user credentials are valid, redirects to the DashboardPage.
          - If invalid, redirects to an ErrorPage.
        """
        form = LoginForm(request.POST)
        if not form.is_valid():
            return render(request, "LoginPage.html", {"form": form})
        
        username = request.POST.get('user')
        password = request.POST.get('password')
        user = self.auth_manager.validate_user(username, password)

        if user:
            return redirect('Dashboard_Page')
        else:
            return redirect('Error_Page')

"""Note: The actual implementation of AuthManager and the templates for LoginPage, DashboardPage, and ErrorPage a
re assumed to be defined elsewhere in the project."""