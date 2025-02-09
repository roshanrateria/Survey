from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from django.forms import inlineformset_factory
from .models import Survey, Question, Choice

class UserRegisterForm(UserCreationForm):
    email = forms.EmailField(required=True)
    
    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2']

class SurveyForm(forms.ModelForm):
    class Meta:
        model = Survey
        fields = ['title', 'description']

class QuestionForm(forms.ModelForm):
    # Extra field for choices: enter choices separated by commas.
    choices_field = forms.CharField(
        widget=forms.Textarea(attrs={'rows': 3, 'placeholder': 'Enter choices separated by commas'}),
        required=True,
        help_text="Enter choices separated by commas."
    )

    class Meta:
        model = Question
        fields = ['text']

    def __init__(self, *args, **kwargs):
        super(QuestionForm, self).__init__(*args, **kwargs)
        # If editing an existing question, pre-populate the choices_field.
        if self.instance.pk:
            self.fields['choices_field'].initial = ", ".join(
                [choice.text for choice in self.instance.choices.all()]
            )

# Inline formset for Questions within a Survey.
QuestionFormSet = inlineformset_factory(
    Survey, Question, form=QuestionForm, extra=1, can_delete=True
)
