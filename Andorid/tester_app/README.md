# tester_app

A new Flutter project.

## Dev Notes

### Entry
1. load preference (general model)
2. refresh JWTs
   - Yes: 
     1. refresh accessToken, refreshToken
     2. get user profile
   - No:
     1. clear cached user profile
     2. set profile to null
3. build homepage

### Home Page
1. check whether profile is null
   - Yes: navigate to login page
   - No : fetch records
> [!NOTE]
> profile is not null from here
1. save profile

### Registration Page
1. try login when "login/create account" button clicked
   - 200 success:
     1. get accessToken, refreshToken
     2. get user profile
   - 404 no user: navigate to create account
   - else: show msg
