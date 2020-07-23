import framework
# unique to module
import re
import time

class Module(framework.module):

    def __init__(self, params):
        framework.module.__init__(self, params)
        self.register_option('username', None, 'yes', 'Username to validate')
        self.info = {
                     'Name': 'Dev Diver Repository Activity Examiner',
                     'Author': 'Micah Hoffman (@WebBreacher)',
                     'Description': 'This module takes a username and searches common, public code repositories for information about that username.',
                     'Comments': []
                     }
    
    def module_run(self):
        username = self.options['username']['value']
        tdata = [['Site', 'Parameter', 'Value']]

        ################
        # Github Check
        ################
        url = 'https://github.com/%s' % username
        try: resp = self.request(url)
        except KeyboardInterrupt:
            print ''
            return
        except Exception as e:
            self.error(e.__str__())
            return
       
        # Parse the results
        gitName = re.search('<span itemprop="name">(.+)</span>', resp.text)
        if gitName: 
            self.alert('Github username found - (%s)' % url)
            gitDesc = re.search('<meta name="description" content="(.+)" />', resp.text)
            gitJoin = re.search('<span class="join-date">(.+)</span>', resp.text)
            gitLoc = re.search('<dd itemprop="homeLocation">(.+)</dd>', resp.text)
            gitPersonalUrl = re.search('<dd itemprop="url"><a href="(.+?)" class="url"', resp.text)
            gitAvatar = re.search('<a href="(https://secure.gravatar.com/avatar/.+?);', resp.text)
            tdata.append(['Github', 'Real Name', gitName.group(1)+' ('+url+')'])
            if gitJoin: 
                tdata.append(['Github', 'Join Date', time.strftime('%Y-%m-%d', time.strptime(gitJoin.group(1), '%b %d, %Y'))])
            if gitLoc: tdata.append(['Github', 'Home Location', gitLoc.group(1)])
            if gitDesc: tdata.append(['Github', 'Description', gitDesc.group(1)])
            if gitPersonalUrl: tdata.append(['Github', 'Personal URL', gitPersonalUrl.group(1)])
            if gitAvatar: tdata.append(['Github', 'Avatar', gitAvatar.group(1)])
        else:
            self.output('Github username not found')
        
        ##################
        #Bitbucket Check
        ##################
        
        # Bitbucket usernames are case sensitive, or at least will do a redirect if not using correct case
        # First we just use the username entered by the recon-ng user
        url = 'https://bitbucket.org/%s' % username
        try: resp = self.request(url)
        except KeyboardInterrupt:
            print ''
            return
        except Exception as e:
            self.error(e.__str__())
            return 
        
        # Parse the results
        bbName = re.search('<h1 title="Username:.+">(.+)</h1>', resp.text)      
        if not bbName:
            # Before we give up on the user not being on Bitbucket, let's search
            urlSearch = 'https://bitbucket.org/repo/all?name=%s' % username
            try: respSearch = self.request(url)
            except KeyboardInterrupt:
                print ''
                return
            except Exception as e:
                self.error(e.__str__())
                return
                
            # Parse the results
            bbUserName = re.search('<a class="repo-link" href="/(.+)/', respSearch.text)
            if bbUserName:
                url = 'https://bitbucket.org/%s' % bbUserName
                try: resp = self.request(url)
                except KeyboardInterrupt:
                    print ''
                    return
                except Exception as e:
                    self.error(e.__str__())
                    return 
                # At least one repository found. Capture username case
                bbName = re.search('<h1 title="Username:.+">(.+)</h1>', resp.text)
                
        # If there is a user there, get info about their account
        if bbName:
            self.alert('Bitbucket username found - (%s)' % url)
            bbJoin = re.search('Member since <time datetime="(.+)T', resp.text)
            bbReposCount = re.search('<span class="count">([0-9]+)</span> Repositories', resp.text)
            bbFollowerCount = re.search('<span class="count">([0-9]+)</span> Followers', resp.text)
            bbFollowingCount = re.search('<span class="count">([0-9]+)</span> Following', resp.text)
            bbRepositories = re.findall('repo-link".+">(.+)</a></h1>', resp.text)
            tdata.append(['Bitbucket', 'Real Name', bbName.group(1)+' ('+url+')'])
            if bbJoin: tdata.append(['Bitbucket', 'Join Date', bbJoin.group(1)])
            if bbFollowerCount and int(bbFollowerCount.group(1)) > 0: 
                tdata.append(['Bitbucket', '# of Followers', bbFollowerCount.group(1)])
            if bbFollowingCount and int(bbFollowingCount.group(1)) > 0: 
                tdata.append(['Bitbucket', '# Projects Following', bbFollowingCount.group(1)])
            if bbRepositories: tdata.append(['Bitbucket', 'Repository Names', ', '.join(bbRepositories)])
        else:
            self.output('Bitbucket username not found')
        
        #####################
        # Sourceforge Check
        #####################
        url = 'http://sourceforge.net/users/%s' % username
        try: resp = self.request(url)
        except KeyboardInterrupt:
            print ''
            return
        except Exception as e:
            self.error(e.__str__())
            return
        
        # Parse the results
        sfName = re.search('<label>Public Name:</label> (.+) </li>', resp.text)
        if sfName: 
            self.alert('Sourceforge username found - (%s)' % url)
            sfJoin = re.search('<label>Joined:</label> (\d\d\d\d-\d\d-\d\d) ', resp.text)
            sfRepositories = re.findall('<li class="item"><a href="/projects/.+>(.+)</a>', resp.text)
            sfMyOpenID = re.search('(?s)<label>My OpenID:</label>.+?<a href="(.+?)"', resp.text)
            tdata.append(['Sourceforge', 'Real Name', sfName.group(1)+' ('+url+')'])
            if sfJoin: tdata.append(['Sourceforge', 'Join Date', sfJoin.group(1)])
            if sfMyOpenID: tdata.append(['Sourceforge', 'Open ID URL', sfMyOpenID.group(1)])
            if sfRepositories: tdata.append(['Sourceforge', 'Repository Names', ', '.join(sfRepositories)])
        else:
            self.output('Sourceforge username not found')
        
        #####################
        # CodePlex Check
        #####################
        url = 'http://www.codeplex.com/site/users/view/%s' % username
        try: resp = self.request(url)
        except KeyboardInterrupt:
            print ''
            return
        except Exception as e:
            self.error(e.__str__())
            return
        
        # Parse the results
        cpName = re.search('<h1 class="user_name" style="display: inline">(.+)</h1>', resp.text)
        if cpName: 
            self.alert('CodePlex username found - (%s)' % url)
            cpJoin = re.search('Member Since<span class="user_float">([A-Z].+[0-9])</span>', resp.text)
            cpLast = re.search('Last Visit<span class="user_float">([A-Z].+[0-9])</span>', resp.text)
            cpCoordinator = re.search('(?s)<p class="OverflowHidden">(.*?)</p>', resp.text)
            tdata.append(['CodePlex', 'URL', url])
            if cpJoin: 
                tdata.append(['CodePlex', 'Join Date', time.strftime('%Y-%m-%d', time.strptime(cpJoin.group(1), '%B %d, %Y'))])
            if cpLast: 
                tdata.append(['CodePlex', 'Last Date', time.strftime('%Y-%m-%d', time.strptime(cpLast.group(1), '%B %d, %Y'))])
            if cpCoordinator: 
                cpCoordProject = re.findall('<a href="(http://.+)/" title=".+">(.+)<br /></a>', cpCoordinator.group(1))
                cpReposOut = []
                for cpReposUrl, cpRepos in cpCoordProject:
                    tdata.append(['CodePlex', 'Coordinator for', cpRepos + ' (' + cpReposUrl + ')'])
        else:
            self.output('CodePlex username not found')
              
        #####################
        # Freecode Check
        #####################
        url = 'http://freecode.com/users/%s' % username
        try: resp = self.request(url)
        except KeyboardInterrupt:
            print ''
            return
        except Exception as e:
            self.error(e.__str__())
            return
        
        # Parse the results
        fcCreated = re.search('(?s)<dt>Created</dt>.+?<dd>(\d\d.+:\d\d)</dd>', resp.text)
        if fcCreated: 
            self.alert('Freecode username found - (%s)' % url)
            fcRepositories = re.findall("'Projects', 'Website', '(.+?)'", resp.text)
            tdata.append(['Freecode', 'URL', url])
            tdata.append(['Freecode', 'Join Date', time.strftime('%Y-%m-%d', time.strptime(fcCreated.group(1), '%d %b %Y %H:%M'))])
            if fcRepositories: tdata.append(['Freecode', 'Repository Names', ', '.join(fcRepositories)])
        else:
            self.output('Freecode username not found')     
 
        #####################
        # Google Code Check
        #####################
        url = 'https://code.google.com/u/%s/' % username
        try: resp = self.request(url)
        except KeyboardInterrupt:
            print ''
            return
        except Exception as e:
            self.error(e.__str__())
            return
        
        # Parse the results
        gooEmail = re.search('(?s)<b>Username: </b>\s.+<span>\s+(.+?)\s+</span>', resp.text)
        if gooEmail: 
            self.alert('Google Code username found - (%s)' % url)            
            gooPlusUrl = re.search('<g:plus href="(.+?)"', resp.text)
            gooRepositoriesOwned = re.findall('(?s)name="owner">.+?<a href="/p/(.+?)/"', resp.text)
            gooRepositoriesCommit = re.findall('(?s)name="committer">.+?<a href="/p/(.+?)/"', resp.text)
            if gooPlusUrl: 
                # Go get user's full name
                try: respGPlus = self.request(gooPlusUrl.group(1)+'/about')
                except Exception as e:
                    self.error(e.__str__())
                    return
                gooName = re.search('<title>(.+?) -.+</title>', respGPlus.text)
                # TODO - Since we are now on this user's G+ page we could scrape a lot more information
                if gooName: tdata.append(['Google Code', 'Full Name', gooName.group(1)])
                tdata.append(['Google Code', 'Google Plus URL', gooPlusUrl.group(1)])
            
            tdata.append(['Google Code', 'Email', gooEmail.group(1)])    
            if gooRepositoriesOwned: tdata.append(['Google Code', 'Repositories Owned', ', '.join(gooRepositoriesOwned)])
            if gooRepositoriesCommit: tdata.append(['Google Code', 'Repository Committer', ', '.join(gooRepositoriesCommit)])
        else:
            self.output('Google code username not found')     
        
        # Print Final Output Table
        if len(tdata) > 1: 
            self.table(tdata, True)
        else:
            self.error('%s not found at any repository' % username)
