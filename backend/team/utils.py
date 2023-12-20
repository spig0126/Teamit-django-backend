def get_team_members_with_creator_first(team):
     members = team.members.all()
     creator = members.filter(pk=team.creator).first()
     members = [creator] + [member for member in members if member != creator]
     
     return members