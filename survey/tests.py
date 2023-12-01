from django.test import TestCase
from django.urls import reverse
from django.contrib.auth.models import User
from survey.models import Question, Answer
import json

class QuestionCreateViewTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user('testuser', 'test@example.com', '12345')
        self.client.login(username='testuser', password='12345')

        self.question = Question.objects.create(title='Test Question', description='Test Description', author=self.user)

        self.QUESTION_CREATE_URL = reverse('survey:question-create')

    # Visualizar
    def test_view_url_exists_at_desired_location(self):
        response = self.client.get('/question/add')
        self.assertEqual(response.status_code, 200)

    def test_view_url_accessible_by_name(self):
        response = self.client.get(self.QUESTION_CREATE_URL)
        self.assertEqual(response.status_code, 200)

    def test_redirect_if_not_logged_in(self):
        self.client.logout()
        response = self.client.get(self.QUESTION_CREATE_URL)
        self.assertRedirects(response, '/accounts/login/?next='+self.QUESTION_CREATE_URL)

    # Crear
    def test_create_question(self):
        question_data = {
            'title': 'Title Question',
            'description': 'Description Question'
        }

        response = self.client.post(self.QUESTION_CREATE_URL, question_data)

        self.assertEqual(Question.objects.count(), 2)
        new_question = Question.objects.last()
        self.assertEqual(new_question.title, 'Title Question')
        self.assertEqual(new_question.description, 'Description Question')
        self.assertEqual(new_question.author, self.user)

        self.assertRedirects(response, reverse('survey:question-list'))

    # Validar Value
    def test_answer_question(self):
        answer_data = {
            'question_pk': self.question.pk,
            'value': 1
        }

        response = self.client.post(reverse('survey:question-answer'), json.dumps(answer_data), content_type='application/json')

        self.assertEqual(Answer.objects.count(), 1)
        answer = Answer.objects.first()
        self.assertEqual(answer.question, self.question)
        self.assertEqual(answer.author, self.user)
        self.assertEqual(answer.value, 1)

        self.assertEqual(response.status_code, 200)
        self.assertIn('questions', response.json())
