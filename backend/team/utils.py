import os

def team_image_upload_path(instance, filename):
    team_pk = instance.pk
    filename, extension = os.path.splitext(filename)
    return f'teams/{team_pk}/main/{filename}{extension}'

def get_team_members_with_creator_first(team):
     members = team.members.all()
     creator = members.filter(pk=team.creator).first()
     members = [creator] + [member for member in members if member != creator]
     
     return members