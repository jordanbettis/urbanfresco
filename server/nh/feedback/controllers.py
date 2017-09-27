from nh.core.controllers import Controller
from nh.core.templates import (
    render_response, forbidden, escape_and_break, found_redirect)

from nh.auth.decorators import permission_required
from nh.feedback.models import FeedbackItem

from sqlalchemy.sql.expression import desc

class FeedbackController(Controller):
    def get_routes(self):
        return [
            self.make_route(
                "feedback-list", "/feedback/list", self.list),
            self.make_route(
                "feedback-view", "/feedback/view/{id}", self.view),
            self.make_form_route(
                "feedback-submit", "/feedback/submit",
                "/feedback/submit.html", self.SubmitForm),
            self.make_route(
                "feedback-publish", "/feedback/publish", self.publish),
            self.make_route(
                "feedback-unpublish", "/feedback/unpublish", self.unpublish),
            self.make_route(
                "feedback-dismiss", "/feedback/dismiss", self.dismiss),
            ]

    def list(self, request):
        """ Display the feedback that's been published on the site """
        v = request.vars
        v.has_admin_perm = request.user.has_permission(
            service="feedback-admin")
        if v.has_admin_perm:
            
            v.unpublished_feedback = request.session.query(FeedbackItem)\
                .filter(FeedbackItem.published==False)\
                .filter(FeedbackItem.dismissed==False)\
                .order_by(desc(FeedbackItem.created))

            v.dismissed_feedback = request.session.query(FeedbackItem)\
                .filter(FeedbackItem.published==False)\
                .filter(FeedbackItem.dismissed==True)\
                .order_by(desc(FeedbackItem.created))

        v.published_feedback = request.session.query(FeedbackItem)\
            .filter(FeedbackItem.published==True)\
            .order_by(desc(FeedbackItem.created))
        
        return render_response("/feedback/list.html", request)

    @permission_required(service="feedback-admin")
    def view(self, request, id):
        """ The view action is only for admins to see past items """
        request.vars.has_admin_perm = request.user.has_permission(
            service="feedback-admin")
        request.vars.feedback = request.session.query(FeedbackItem).get(id)
        return render_response("/feedback/feedback.html", request)

    class SubmitForm(Form):
        """ Allow a user to write a feedback item """
        name = fields.TextField("Your name", [
                validators.Length(min=3, max=200)])
        email = fields.TextField("Email (optional)", [
                validators.Optional(), validators.Email()])
        can_publish = fields.BooleanField(
            "Yes! You may publish this message.")
        message = fields.TextAreaField()

        @classmethod
        def permission(cls, request):
            return None

        @classmethod
        def initialize_get(cls, request):
            return cls(name=request.user.data.get("display-name", ""),
                       email=request.user.email)

        def save(self, request):
            feedback = FeedbackItem(
                name = self.name.data,
                email = self.email.data,
                can_publish = self.can_publish.data,
                message = self.message.data,
                user=request.user)
            request.session.add(feedback)

            return found_redirect(request, request.url_for("feedback-list"))

    @permission_required(service="feedback-admin")
    def publish(self, request):
        """ Set public viewability of a feedback item  """
        feedback = request.session.query(FeedbackItem).get(request.GET['id'])
        if feedback.can_publish:
            feedback.published = True
        else:
            return forbidden(request)

        return found_redirect(request, request.url_for("feedback-list"))
                    
    @permission_required(service="feedback-admin")
    def unpublish(self, request):
        """ Unset public viewability """
        feedback = request.session.query(FeedbackItem).get(request.GET['id'])
        feedback.published = False

        return found_redirect(request, request.url_for("feedback-list"))

    @permission_required(service="feedback-admin")
    def dismiss(self, request):
        """ Dismiss an item from the feedback list """
        feedback = request.session.query(FeedbackItem).get(request.GET['id'])
        feedback.dismissed = True

        return found_redirect(request, request.url_for("feedback-list"))
