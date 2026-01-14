"""
Кастомные обработчики ошибок
"""
from django.shortcuts import render


def handler400(request, exception=None):
    """Обработчик ошибки 400 - Некорректный запрос"""
    return render(request, '400.html', status=400)


def handler403(request, exception=None):
    """Обработчик ошибки 403 - Доступ запрещён"""
    return render(request, '403.html', status=403)


def handler404(request, exception=None):
    """Обработчик ошибки 404 - Страница не найдена"""
    return render(request, '404.html', status=404)


def handler500(request):
    """Обработчик ошибки 500 - Внутренняя ошибка сервера"""
    return render(request, '500.html', status=500)
