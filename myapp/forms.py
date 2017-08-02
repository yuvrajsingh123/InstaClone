from django import forms
from models import UserModel, PostModel, LikeModel, CommentModel

#creating a signup form
class SignUpForm(forms.ModelForm):
    class Meta:
        model = UserModel
        fields=['email','username','name','password']


#creating a Login form
class LoginForm(forms.ModelForm):
    class Meta:
        model = UserModel
        fields = ['username', 'password']


#creating a Post form
class PostForm(forms.ModelForm):
    class Meta:
        model = PostModel
        fields=['image', 'caption']



#creating a Like form
class LikeForm(forms.ModelForm):

    class Meta:
        model = LikeModel
        fields=['post']



#creating a Comment form
class CommentForm(forms.ModelForm):

    class Meta:
        model = CommentModel
        fields = ['comment_text', 'post']


#creating a Upvote form
class UpvoteForm(forms.Form):
    id = forms.IntegerField()



#creating a Search form
class SearchForm(forms.Form):
    searchquery = forms.CharField();
