from django.shortcuts import render, get_object_or_404
from .models import Post, Comment
from django.conf import settings
from django.http import Http404
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger

from django.views.generic import ListView

from .forms import EmailPostForm, CommentForm
from django.core.mail import send_mail
from django.views.decorators.http import require_POST
from taggit.models import Tag

# Create your views here.


class PostListView(ListView):

    queryset = Post.published.all()
    context_object_name = 'posts'
    paginate_by = 3
    template_name = 'blog/post_list.html'


def post_list(request, tag_slug=None):
    post_list = Post.published.all()
    tag = None
    if tag_slug:
        tag = get_object_or_404(Tag, slug=tag_slug)
        post_list = post_list.filter(tags__in=[tag])
    paginator = Paginator(post_list, 3)
    page_number = request.GET.get('page')
    try:
        posts = paginator.get_page(page_number)

    except PageNotAnInteger:
        posts = paginator.get_page(1)

    except EmptyPage:
        posts = paginator.get_page(paginator.num_pages)
    return render(request, 'blog/post_list.html', {'posts': posts})


def post_detail(request, year, month, day, post):
    post = get_object_or_404(Post, status=Post.Status.PUBLISHED, slug=post,
                             publish__year=year,
                             publish__month=month,
                             publish__day=day)

    comments = post.comments.filter(active=True)
    form = CommentForm()
    return render(request, 'blog/post/detail.html', {'post': post,
                                                     'comments': comments,
                                                     'form': form}

                  )


def post_share(request, post_id):

    post = get_object_or_404(Post, id=post_id, status=Post.Status.PUBLISHED)
    if request.method == 'POST':
        # form was submitted

        form = EmailPostForm(request.POST)
        if form.is_valid():

            cd = form.cleaned_data

            # send email
            from_email = settings.EMAIL_HOST_USER
            post_url = request.build_absolute_uri(post.get_absolute_url())
            subject = f"{cd['name']} recommends you read {post.title}"
            message = f"Read {post.title} at {post_url} comment: {['comments']}"

            send_mail(subject, message, from_email, [cd['to']])
            send_mail.send(fail_silently=False)
            sent = True

    else:
        form = EmailPostForm

    return render(request, 'blog/post/share.html', {'post': post,
                                                    'form': form})


@require_POST
def post_comment(request, post_id):
    post = get_object_or_404(Post, id=post_id, status=Post.Status.PUBLISHED)
    comment = None
    form = CommentForm(data=request.POST)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.post = post
        comment.save()

    return render(request, 'blog/post/comment.html', {'post': post,
                                                      'form': form,
                                                      'comment': comment})
