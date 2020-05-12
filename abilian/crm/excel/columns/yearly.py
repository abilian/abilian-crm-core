""""""

from .related import ManyRelatedColumnSet


class ManyYearlyColumnSet(ManyRelatedColumnSet):
    def __init__(self, related_attr="ignored", *args, **kwargs):
        super().__init__(
            related_attr="__yearly_data__", *args, **kwargs
        )

    def iter_items(self, obj):
        yield from getattr(obj, self.related_attr).values()
