from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from .forms import UserRegisterForm, SurveyForm, QuestionFormSet, QuestionForm
from .models import Survey, Question, Choice, Response, Answer
from django.forms import inlineformset_factory

# --- Authentication Views (unchanged) --
def index(request):
    """
    Default view: if user is authenticated, redirect to the survey list,
    otherwise redirect to the registration page.
    """
    if request.user.is_authenticated:
        return redirect('survey_list')
    else:
        return redirect('register')
def register(request):
    if request.method == 'POST':
        form = UserRegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            messages.success(request, 'Registration successful. You can now log in.')
            return redirect('login')
    else:
        form = UserRegisterForm()
    return render(request, 'registration.html', {'form': form})

def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('survey_list')
        else:
            messages.error(request, 'Invalid username or password')
    return render(request, 'login.html')

@login_required
def logout_view(request):
    logout(request)
    return redirect('login')

# --- Survey and Response Views (unchanged) ---
@login_required
def survey_list(request):
    surveys = Survey.objects.all()
    return render(request, 'survey_list.html', {'surveys': surveys})

@login_required
def survey_detail(request, survey_id):
    survey = get_object_or_404(Survey, pk=survey_id)
    # Increment visited count on GET requests.
    if request.method == 'GET':
        survey.visited += 1
        survey.save()
    if request.method == 'POST':
        response = Response.objects.create(survey=survey, user=request.user)
        for question in survey.questions.all():
            choice_id = request.POST.get(str(question.id))
            if choice_id:
                choice = get_object_or_404(Choice, pk=choice_id)
                Answer.objects.create(response=response, question=question, choice=choice)
        messages.success(request, 'Your responses have been recorded.')
        return redirect('survey_statistics', survey_id=survey.id)
    return render(request, 'survey_detail.html', {'survey': survey})

@login_required
def survey_statistics(request, survey_id):
    survey = get_object_or_404(Survey, pk=survey_id)
    stats = []
    for question in survey.questions.all():
        question_stats = []
        for choice in question.choices.all():
            count = Answer.objects.filter(question=question, choice=choice).count()
            question_stats.append({'choice': choice.text, 'count': count})
        stats.append({
            'question_text': question.text,
            'chart_type': question.chart_type,
            'data': question_stats,
        })
    total_submissions = survey.responses.count()
    return render(request, 'survey_statistics.html', {
        'survey': survey,
        'stats': stats,
        'total_submissions': total_submissions
    })
def admin_check(user):
    return user.is_staff

@login_required
@user_passes_test(lambda u: u.is_staff)
def survey_responses(request, survey_id):
    survey = get_object_or_404(Survey, pk=survey_id)
    responses = survey.responses.all()
    total_visited = survey.visited
    return render(request, 'survey_responses.html', {
        'survey': survey,
        'responses': responses,
        'total_visited': total_visited
    })
# --- Updated Admin-only Views for Creating and Editing Surveys ---

@login_required
@user_passes_test(lambda u: u.is_staff)
def survey_create(request):
    # Use extra=1 so one blank question appears by default, and set an explicit prefix.
    QuestionFormSetCreate = inlineformset_factory(
        Survey, Question, form=QuestionForm, extra=1, can_delete=True
    )
    if request.method == 'POST':
        survey_form = SurveyForm(request.POST)
        question_formset = QuestionFormSetCreate(request.POST, prefix='questions')
        if survey_form.is_valid() and question_formset.is_valid():
            survey = survey_form.save(commit=False)
            survey.created_by = request.user
            survey.save()
            question_formset.instance = survey
            for form in question_formset:
                if form.cleaned_data and not form.cleaned_data.get('DELETE', False):
                    question = form.save(commit=False)
                    question.survey = survey
                    question.save()
                    choices_text = form.cleaned_data.get('choices_field')
                    if choices_text:
                        choices = [c.strip() for c in choices_text.split(',') if c.strip()]
                        for choice_text in choices:
                            Choice.objects.create(question=question, text=choice_text)
            messages.success(request, 'Survey created successfully.')
            return redirect('survey_list')
    else:
        survey_form = SurveyForm()
        question_formset = QuestionFormSetCreate(prefix='questions')
    return render(request, 'survey_create.html', {
        'form': survey_form,
        'question_formset': question_formset
    })

@login_required
@user_passes_test(lambda u: u.is_staff)
def survey_edit(request, survey_id):
    survey = get_object_or_404(Survey, pk=survey_id)
    # Use extra=0 so no blank question shows by default, and use prefix 'questions'
    QuestionFormSetLocal = inlineformset_factory(
        Survey, Question, form=QuestionForm, extra=0, can_delete=True
    )
    if request.method == 'POST':
        survey_form = SurveyForm(request.POST, instance=survey)
        question_formset = QuestionFormSetLocal(request.POST, instance=survey, prefix='questions')
        if survey_form.is_valid() and question_formset.is_valid():
            survey = survey_form.save()
            for form in question_formset:
                if form.cleaned_data:
                    if form.cleaned_data.get('DELETE', False):
                        if form.instance.pk:
                            form.instance.delete()
                    else:
                        question = form.save(commit=False)
                        question.survey = survey
                        question.save()
                        new_choices_text = form.cleaned_data.get('choices_field')
                        new_choices_list = [c.strip() for c in new_choices_text.split(',') if c.strip()]
                        old_choices_list = [c.text.strip() for c in question.choices.all()]
                        if sorted(old_choices_list) != sorted(new_choices_list):
                            question.choices.all().delete()
                            for choice_text in new_choices_list:
                                Choice.objects.create(question=question, text=choice_text)
            messages.success(request, 'Survey updated successfully.')
            return redirect('survey_list')
    else:
        survey_form = SurveyForm(instance=survey)
        question_formset = QuestionFormSetLocal(instance=survey, prefix='questions')
    return render(request, 'survey_edit.html', {
        'form': survey_form,
        'question_formset': question_formset,
        'survey': survey
    })
@login_required
@user_passes_test(admin_check)
def survey_delete(request, survey_id):
    survey = get_object_or_404(Survey, pk=survey_id)
    if request.method == 'POST':
        survey.delete()
        messages.success(request, 'Survey deleted successfully.')
        return redirect('survey_list')
    return render(request, 'survey_delete_confirm.html', {'survey': survey})
