from django.views.generic.base import TemplateView


#  View-класс для страницы об авторе
class AboutAuthorView(TemplateView):
    template_name = 'about/author.html'


#  View-класс для страницы об авторе
class AboutTechView(TemplateView):
    template_name = 'about/tech.html'
