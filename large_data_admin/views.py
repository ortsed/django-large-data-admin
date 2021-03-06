import urllib, json

from django.http import HttpResponse
from django.template.defaultfilters import slugify
from django.shortcuts import render_to_response, render
from django.conf import settings
from django.db.models import Q
from operator import __or__ as OR

from helpers import get_model

def get_json(request):
    model_str = request.GET.get("model")
    fields = request.GET.get("field").split(",")
    query = urllib.unquote(request.GET.get("query", ""))
    exclude = filter(None, request.GET.get("exclude", "").split(","))
    fromlist = filter(None, request.GET.get("fromlist", "").split(","))
    unique = request.GET.get("unique")
    try:
        filter_query  = json.loads(urllib.unquote(request.GET.get("filter_query")))
    except:
        filter_query = {}
    try:
        exclude_query = json.loads(urllib.unquote(request.GET.get("exclude_query")))
    except:
        exclude_query = {}

    Model = get_model(model_str)

    if (len(filter_query) + len(exclude_query)) == 0:
        filter_query = [Q(**{"%s__icontains"%field: query}) for field in fields]
        #filter_query = {"%s__icontains"%field: query}
        exclude_query = {"pk__in": exclude}

    if fromlist:
        filter_query.update({"pk__in": fromlist })

    qs = Model.objects.filter(reduce(OR, filter_query)).exclude(**exclude_query)

    if unique:
        try:  # XXX: needs prety check if DISTINCT is available, ticket #3
            return HttpResponse(json.dumps(list(qs.distinct(*fields).values_list("pk", *fields).order_by(fields[0]))))
        except NotImplementedError:
            data = []
            unique_by_field = []
            for val in list(qs.values_list("pk", *fields)):
                if val not in unique_by_field:
                    data.append((val))
                unique_by_field.append(val)
            return HttpResponse(json.dumps(data))
    return HttpResponse(json.dumps(list(qs.values_list("pk", *fields))))

def m2m_list_view(request, model_str):
    pks = [int(pk) for pk in filter(None, request.GET.get("q", "").split(","))]
    Model = get_model(model_str)
    objs = Model.objects.filter(pk__in=pks)

    return render(request, "large_data_admin/m2m/list.html", {
        "objs": objs,
    })

def m2m_remove_view(request, model_str):
    pks = [int(pk) for pk in filter(None, request.GET.get("q", "").split(","))]
    Model = get_model(model_str)
    objs = Model.objects.filter(pk__in=pks)

    return render(request, "large_data_admin/m2m/remove.html", {
        "objs": objs,
    })
