from django.contrib import messages
from django.db.models.deletion import ProtectedError
from django.http import HttpResponseRedirect, JsonResponse


class ProtectedErrorMiddleware:
    """Convert uncaught ProtectedError into user-friendly responses."""

    def __init__(self, get_response):
        self.get_response = get_response

    @staticmethod
    def _build_message(exc):
        protected = list(getattr(exc, 'protected_objects', []) or [])
        if not protected:
            return 'Khong the xoa do con du lieu lien quan trong he thong.'

        labels = []
        for obj in protected[:5]:
            meta = getattr(obj, '_meta', None)
            model_name = meta.verbose_name if meta else obj.__class__.__name__
            labels.append(f'{model_name}: {obj}')
        if len(protected) > 5:
            labels.append('...')
        return 'Khong the xoa do con du lieu lien quan: ' + '; '.join(labels)

    def __call__(self, request):
        try:
            return self.get_response(request)
        except ProtectedError as exc:
            message = self._build_message(exc)

            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({'error': message}, status=409)

            messages.error(request, message)
            target = request.META.get('HTTP_REFERER') or '/'
            return HttpResponseRedirect(target)
