from datetime import datetime, date, timedelta

from nh.core.controllers import Controller
from nh.core.templates import (
    render_response, forbidden, found_redirect, render_string, escape_and_break)
from nh.auth.models import User
from nh.auth.decorators import authentication_required
from nh.auth.utils import authentication_redirect
from nh.core import mail
from nh.core.config import CONFIG

from sqlalchemy.orm.exc import NoResultFound
from sqlalchemy.exc import IntegrityError

from wtforms import fields, validators
from wtforms.ext.dateutil.fields import DateField
from wtforms.form import Form

import random

class UserController(Controller):
    def get_routes(self):
        return [
            self.make_form_route(
                "auth-login", "/auth/login", "/auth/login.html", self.LoginForm),
            
            self.make_route("auth-logout", "/auth/logout", self.logout),
            self.make_form_route("auth-verify", "/auth/verify",
                                 "/auth/verify.html", self.VerifyForm),
            
            self.make_route("auth-confirm", "/auth/confirm/{key}", self.confirm),
            self.make_route("auth-put-avatar", "/auth/put-avatar", self.put_avatar),
            
            self.make_form_route("auth-register", "/auth/register",
                                 "/auth/register.html", self.RegisterForm),
            self.make_form_route(
                "auth-edit-password", "/auth/edit/password",
                "/auth/edit-password.html", self.ChangePassword),
            self.make_form_route("auth-edit-name", "/auth/edit/name",
                                 "/auth/edit-name.html", self.FullName),
            self.make_form_route("auth-edit-profile", "/auth/edit/profile",
                                 "/auth/edit-profile.html", self.Profile),
            ]
    
    class LoginForm(Form):
        """ Login form for using username """
        name = fields.TextField("Username", [validators.Optional()])
        email = fields.TextField("Email Address", [validators.Optional()])
        password = fields.PasswordField("Password")

        @classmethod
        def permission(cls, request):
            return None
        
        def save(self, request):
            if not self.email.data and not self.name.data:
                raise validators.ValidationError(
                    "You must provide a username or email")
                
            if self.name.data:
                user = request.session.query(
                    User).filter_by(name=self.name.data.lower()).first()
            else:
                user = request.session.query(
                    User).filter_by(email=self.email.data).first()

            if user == None:
                request.vars.errors.append("Authentication failure")
                raise validators.ValidationError

            if not user.login(request, self.password.data):
                raise validators.ValidationError("Authentication failure")
            else:
                response = _userroot_redirect(request)
                user.session_key = user.new_session_key()
                response.set_cookie("nh-session", user.session_key)
                return response
        
    def logout(self, request):
        """ Log the current user out """
        if request.user.authenticated:
            request.user.logout()
            
        return found_redirect(
            request, request.GET.get("return", "/"))

    @authentication_required
    def put_avatar(self, request):
        """ Upload an avatar image """
        user = request.user

        file_field = request.POST.get('files[]')
        if file_field == None:
            return not_found(request)

        user.unlink_avatar()
        user.data['avatar-key'] = "".join([choice("0123456789") for x in range(29)])
        user.data['avatar-filename'] = file_field.filename
        user.data['avatar-type'] = file_field.type
        user.data['avatar-type-options'] = file_field.type_options
        user.data['avatar-ext'] = os.path.splitext(file_field.filename)[1]

        upload_fd = open(user.avatar_upload_path, 'w')
        upload_fd.write(file_field.file.read())
        upload_fd.close()
 
        user.generate_avatar_sizes()
        
        cache.set("user-info-%s" % request.user.name, request.user.info, 180)
        
        response_data = [
                {"name": user.data.get('avatar-key', "") + ".jpg",
                 "url": user.avatar_url("profile"),
                 "thumbnail_url": user.avatar_url("tiny")}]
                
        return Response(content_type="application/json",
                        body=json.dumps(response_data))
        
    class VerifyForm(Form):
        email = fields.TextField("Email", [validators.Email()])
        dob = DateField("Date of Birth", display_format="%m/%d/%Y")

        @classmethod
        def permission(cls, request):
            thirteen = date.today() - timedelta(days=(365 * 13))
            if request.user.dob and request.user.dob >= thirteen:
                return found_redirect(
                    request, request.url_for("staticpage-coppa"))    
            return None

        def save(self, request):
            request.user.dob = self.dob.data
            thirteen = date.today() - timedelta(days=(365 * 13))

            # If the user is less than thirteen we don't record
            # the email or allow them to use verified services
            # to comply with COPPA
            if request.user.dob >= thirteen:
                return found_redirect(
                    request, request.url_for("staticpage-coppa"))
                
            request.session.commit()
            request.user.email = self.email.data
            try:
                request.session.commit()
            except IntegrityError:
                request.vars.errors.append(
                    "That email address is invalid or in use")
                request.session.rollback()
                return None
            
            else:
                request.user.data['verify-key'] = "".join(
                    [random.choice("1234567890") for x in range(12)])
                    
                mail.send(mail.create(
                        request.user.email, "Verify your account",
                        render_string(
                            "/auth/verify-email.txt", request=request)))
                
                return _userroot_redirect(request)

    @authentication_required
    def confirm(self, request, key):
        """ Confirm landing for the above email verification request """
        verify_key = request.user.data.get('verify-key')
        if key == verify_key:
            request.user.verified = True
        
        return render_response("/auth/confirm.html", request)

    class RegisterForm(Form):
        name = fields.TextField("Username", [
                validators.Length(min=3, max=200),
                validators.NoneOf(CONFIG.BANNED_USERNAMES,
                                  "Choose a different username")])
        email = fields.TextField("Email (optional)",
                                 [validators.Optional(), validators.Email()])
        password = fields.PasswordField('New Password', [
                validators.Required(), validators.Length(min=8),
                validators.EqualTo('confirm',
                                   message='Password does not match confirmation')])
        confirm = fields.PasswordField('Repeat Password')

        @classmethod
        def permission(cls, request):
            return None
        
        def save(self, request):
            request.session.commit()
            name = self.name.data.lower()
            new_user = User(
                name=name, registered=True)
            new_user.set_password(self.password.data)
            request.session.add(new_user)

            ## Preserve username capitalization for display
            if name != self.name.data:
                new_user.data['caps-name'] = self.name.data
            
            try:
                request.session.commit()
            except IntegrityError:
                request.vars.errors.append(
                    "A user with this name already exists")
                request.session.rollback()
                raise validators.ValidationError
            else:
                new_user.login(request, self.password.data)
                user_root = request.url_for(
                    "images-userroot", map_username=new_user.name)
                response = _userroot_redirect(request)
                response.set_cookie("nh-session", new_user.session_key)
                return response

    class ChangePassword(Form):
        current_password = fields.PasswordField(
            "Current Password", [validators.Required()])
        password = fields.PasswordField('New Password', [
                validators.Optional(), validators.Length(min=8),
                validators.EqualTo(
                    'confirm', message='Password does not match confirmation')])
        confirm = fields.PasswordField('Repeat New Password')

        @classmethod
        def permission(cls, request):
            return authentication_redirect(request, recent=False)

        def save(self, request):
            if not request.user.authenticate(self.current_password.data):
                raise validators.ValidationError("Current password is invalid")
            request.user.set_password(self.password.data)
            cache.set("user-info-%s" % request.user.name, request.user.info, 180)
            return _userroot_redirect(request)

    class FullName(Form):
        """ Allow a user to change their full name """
        full_name = fields.TextField("Full Name")

        @classmethod
        def permission(cls, request):
            return authentication_redirect(request, recent=False)

        @classmethod
        def initialize_get(cls, request):
            return cls(full_name=request.user.data.get('display-name', ""))

        def save(self, request):
            user = request.user
            user.data['display-name'] = self.full_name.data
            cache.set("user-info-%s" % user.name, user.info, 180)
            return _userroot_redirect(
                request, {"name": user.display_name})

    class Profile(Form):
        """ Users can have a personal profile on their homepage """
        profile = fields.TextAreaField()

        @classmethod
        def permission(cls, request):
            return authentication_redirect(request, recent=False)

        @classmethod
        def initialize_get(cls, request):
            return cls(profile=request.user.data.get('profile', ""))

        def save(self, request):
            user = request.user
            user.data['profile'] = self.profile.data
            cache.set("user-info-%s" % user.name, user.info, 180)
            return _userroot_redirect(
                request, {"profile": escape_and_break(user.data['profile'])}) 
            
        
def _userroot_redirect(request, ajax_data={}):
    """
    Create a found redirect sending the user either to the "complete"
    get parameter or to request-user's root page.
    """
    user_root = request.url_for(
        "images-userroot", map_username=request.user.name)
    return found_redirect(
        request, request.GET.get("complete", user_root), ajax_data)
