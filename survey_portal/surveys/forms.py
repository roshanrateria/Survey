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
    # Extra field to allow admin to enter choices as a comma‐separated list.
    choices_field = forms.CharField(
        widget=forms.Textarea(attrs={'rows': 3, 'placeholder': 'Enter choices separated by commas'}),
        required=True,
        help_text="Enter choices separated by commas."
    )
    # New field for selecting the chart type.
    chart_type = forms.ChoiceField(
        choices=Question.CHART_CHOICES,
        initial='bar',
        required=True,
        help_text="Select the chart type for this question."
    )

    class Meta:
        model = Question
        fields = ['text', 'chart_type']

    def __init__(self, *args, **kwargs):
        super(QuestionForm, self).__init__(*args, **kwargs)
        # Pre-populate choices_field if editing an existing question.
        if self.instance.pk:
            self.fields['choices_field'].initial = ", ".join(
                [choice.text for choice in self.instance.choices.all()]
            )

# Inline formset for Questions within a Survey.
QuestionFormSet = inlineformset_factory(
    Survey, Question, form=QuestionForm, extra=1, can_delete=True
)
