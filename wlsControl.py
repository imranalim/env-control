#+=====================================================================================================+
#| FILENAME                                                                                            |
#|   wlsController.py or wlsControl.py                                                                 |
#|                                                                                                     |
#| VERSION                                                                                             |
#|   v 4.1                                                                                             |
#|                                                                                                     |
#| DESCRIPTION                                                                                         |
#|   Python script to automate start/stop/rollbounce of WLS                                            |
#|                                                                                                     |
#| SYNTAX                                                                                              |
#|   Syntax1:                                                                                          |
#|           . ${WL_HOME}/server/bin/setWLSEnv.sh                                                      |
#|           java weblogic.WLST wlsControl.py propFilePrefix DomainName Action OptionalArg             |
#|   Syntax2:                                                                                          |
#|           ${WL_HOME}/common/bin/wlst.sh wlsControl.py propFilePrefix DomainName Action ResourceName |
#|                                                                                                     |
#| AUTHOR                                                                                              |
#|       M. Imran Ali [mohammed.imran.ali@oracle.com]                                                  |
#|                                                                                                     |
#| HISTORY                                                                                             |
#|   v1     01-JUL-2016      Created                                                                   |
#|   v1.1   04-JUL-2016      Fixed Bugs, Added help and syntax                                         |
#|   v1.2   11-JUL-2016      StartFirst and StartLast added                                            |
#|   v1.3   17-JUL-2016      Display change: Remove Loop count display and show servers in single line |
#|   v2.1   17-JUL-2016      Moved some properties from py to prop file                                |
#|   v3.1   26-JUL-2016      Included propFile as 1st arg, Included sslTrustStore in prop file         |
#|   v4.1   06-AUG-2016      Updated host based startup/shutdown,renamed cluster stop/start option     |
#|   v4.2   14-SEP-2016      Add skip/do-not-start managed server list                                 |
#|   v5.1   27-SEP-2016      Added adminCredentialType and nmCredentialType for encrypted pwd          |
#|   v5.2   27-SEP-2016      Added statusManagedServers and statusClusters                             |
#+=====================================================================================================+
#CRMAB:/u04/common/crmscripts/tmp_imran
#/u01/APPLTOP/fusionapps/wlserver_10.3/common/bin/wlst.sh test.py bidomain list
#For Admin operations,
#export WLST_PROPERTIES="-Djavax.net.ssl.trustStore=/u01/APPLTOP/instance/keystores/fusion_trust.jks -Dweblogic.security.SSL.trustedCAKeyStore=/u01/APPLTOP/instance/keystores/fusion_trust.jks"
#Property file name will be <propFilePrefix>.prop e.g. crmad.prop

import sys
import os
import time as pytime
from java.io import FileInputStream
import re
from sets import Set as pySet
from datetime import datetime as mydatetime

#===============Define all functions========================#

def currTime():
   return '['+mydatetime.now().strftime('%Y-%m-%d %H:%M:%S')+']'

def scriptSyntax():
   print '\n[SYNTAX]:'
   print '==================================================================================================================================================='
   print ' <script> [envName/propFilePrefix] [DomainName] [ACTION] [RESOURCE_NAME(optional)]'
   print ' <script> [envName/propFilePrefix] [<DomainName>] [status|list|details|stopAll|startAll|restartAllManServers|stopAllManServers|startAllManServers|stopAdminServer|'
   print '                                  startAdminServer|statusAdminServer|stopManagedServers|startManagedServers|statusManagedServers|stopClusters|startClusters|statusClusters|'
   print '                                  stopManServerContains|startManServerContains|stopClusterContains|startClusterContains|rollBounceAllManServers|rollBounceClusterSerial|'
   print '                                  rollBounceCluster|stopManSvrsOnHosts|startManSvrsOnHosts|bounceManagedServers]  [<Servername>|<ClusterName>|<String>]'
   print ''
   #print 'NOTE: The DomainName is case-insensitive. You may provide a short name of the domain and the closest first match will be picked from prop file.'
   print 'NOTE: The script requires a properties file (<propFilePrefix>.prop), which contains details of the domains-It is present in the same directory as the script.'
   print 'NOTE: The [propFilePrefix] is (usually) the name of the environment.'
   print '==================================================================================================================================================='

def scriptHelp():
   print '\n[ACTION]s :'
   print '=ACTION====================================DESCRIPTION================================================================================'
   print ' status                                   :Get status of all managed servers in domain'
   print ' list                                     :List all servers and clusters in the domain'
   print ' details                                  :Get Details for all servers like status,listenaddress,port,starttime,health,starttime'
   print '                                           ...it can also take a string as input to provide details for matching Managed Servers'
   print ' stopAll                                  :Stop all managed servers in parallel and then Admin server'
   print ' startAll                                 :Start Admin server and then all managed servers in parallel'
   print ' restartAllManServers                     :Stop all managed server in domain in parallel and then start them all'
   print ' stopAllManServers                        :Stop all managed servers in domain in parallel'
   print ' startAllManServers                       :Start all managed servers in domain in parallel'
   print ''
   print ' stopAdminServer                          :Stop Admin server'
   print ' startAdminServer                         :Start Admin server'
   print ' statusAdminServer                        :Display Status of Admin server'
   print ' stopManagedServers <CommaSepSvrNames>    :Stop managed servers passed as 3rd argument'
   print ' startManagedServers <CommaSepSvrNames>   :Start managed servers passed as 3rd argument'
   print ' statusManagedServers <CommaSepSvrNames>  :Status of managed servers passed as 3rd argument'
   print ' bounceManagedServers <CommaSepSvrNames>  :Stop all listed servers in parallel and then start them'
   print ' stopClusters <CommaSepClusterNames>      :Stop clusters passed as argument'
   print ' startClusters <CommaSepClusterNames>     :Start clusters passed as argument'
   print ' statusClusters <CommaSepClusterNames>    :Status of clusters passed as argument'
   print ' stopManServerContains <string>           :Stop all servers in parallel whose name match the string passed'
   print ' startManServerContains <string>          :Start all servers in parallel whose name match the string passed'
   print ' stopClusterContains <string>             :Stop all clusters in parallel whose name match the string passed'
   print ' startClusterContains <string>            :Start all servers in parallel whose name match the string passed'
   print ''
   print ' rollBounceAllManServers                  :Roll-bounce all servers in the domain one by one'
   print ' rollBounceClusterSerial <ClstrName>      :Roll-bounce all servers in specified cluster one-by-one'
   print ' rollBounceCluster <ClstrName>            :Roll-bounce all servers in specified cluster - The servers will be divided into ...'
   print '                                           ...two parts - Part1 will be stopped and then started in parallel; followed by Part2'
   print ' stopManSvrsOnHosts <CommaSepHostList>    :Stop all managed servers configured on the listed hosts in parallel'
   print ' startManSvrsOnHosts <CommaSepHostList>   :Start all managed servers configured on the listed hosts in parallel'
   print ''
   print 'Note: All arguments to the script are case-sensitive, except DomainName - it will pick the closest match from prop file.'
   print 'Note: In cases where comma separated list needs to be provided, ensure there are NO spaces in between. If only one entry, then comma not required.'
   print '==================================================================================================================================='

def getManServersInDomain():
   domainConfig()
   allServerList=[]
   serverArray = cmo.getServers()
   AdminServerName = cmo.getAdminServerName()
   for svr in serverArray:
      svrName=svr.getName()
      if svrName != AdminServerName:
         allServerList.append(svrName)
   allServerList.sort()
   return allServerList

def getClustersInDomain():
   domainConfig()
   clusterList=[]
   clusterArray = cmo.getClusters()
   for clstr in clusterArray:
      clstrName=clstr.getName()
      clusterList.append(clstrName)
   clusterList.sort()
   return clusterList
   
def getManServersInCluster(clstrName):
   domainConfig()
   serverInClusterList=[]
   cd ('/Clusters/' + clstrName)
   for svr in cmo.getServers():
      serverInClusterList.append(svr.getName())
   serverInClusterList.sort()
   return serverInClusterList

def getServerStatus(svrName):
   domainRuntime()
   cd('/ServerLifeCycleRuntimes/' + svrName)
   return cmo.getState()

def controlResource(resourceName,resourceType,actionType,returnType):
   ACTIONED = 'NO'
   actionedSvrList=[]
   if resourceType == 'Server':
      svrState=getServerStatus(resourceName)
   domainConfig()
   if actionType == 'stop':
      if resourceType == 'Server' and svrState == 'SHUTDOWN':
         print currTime()+' [' + domainName+ '] Not trying to stop ['+resourceName+'] since it is already in '+svrState+' state.'
      else:
         print currTime()+' [' + domainName+ '] Stopping '+resourceType+': '+resourceName+'...'
         shutdown(resourceName, resourceType, force='true', ignoreSessions='true', block='false')
         ACTIONED = 'YES'
   elif actionType == 'start':
      if resourceType == 'Server' and svrState not in ['SHUTDOWN','FAILED','FAILED_NOT_RESTARTABLE']:
         print currTime()+' [' + domainName+ '] Not trying to start ['+resourceName+'] since it is already in '+svrState+' state.'
      else:
         print currTime()+' [' + domainName+ '] Starting '+resourceType+': '+resourceName+'...'
         start(resourceName, resourceType, block='false')
         ACTIONED = 'YES'
   else:
      print currTime()+' ERROR: Incorrect actionType passed to controlResource function'
   if ACTIONED == 'YES':
      if resourceType == 'Server':
         actionedSvrList.append(resourceName)
      elif resourceType == 'Cluster':
         cd ('/Clusters/' + resourceName)
         for svr in cmo.getServers():
            actionedSvrList.append(svr.getName())
      else:
         print currTime()+' Incorrect resourceType passed to controlResource function.'
   #print 'Debug: '+str(actionedSvrList)
   if len(actionedSvrList) != 0:
      actionedSvrList.sort()
   #print 'Debug: '+str(actionedSvrList)
   if returnType == 'returnList':
      return actionedSvrList
   if returnType == 'waitForJob':
      waitForJobCompletion(actionedSvrList,actionType,'auto')


def controlMatchingResources(resourceNameStr,resourceType,action):
   print '\n'+currTime()+' ['+domainName+'] Initiating '+action+' of all the '+resourceType+'s whose names contain the string ['+resourceNameStr+']...'
   actionedSvrList=[]
   actionedClstrList=[]
   if resourceType == 'Server':
      for svrName in getManServersInDomain():
         if resourceNameStr in svrName:
            actionedSvrList.append(svrName)
      print currTime()+' ['+domainName+'] '+action+' of following servers will be invoked: '+str(actionedSvrList)
      controlListOfManServers(action,actionedSvrList)
   elif resourceType == 'Cluster':
      for clstrName in getClustersInDomain():
         if resourceNameStr in clstrName:
            actionedClstrList.append(clstrName)
      print currTime()+' ['+domainName+'] '+action+' of following clusters will be invoked: '+str(actionedClstrList)
      controlListOfClusters(action,actionedClstrList)

#def controlAllClusters(actionType):
#   try:
#      actionedSvrListAll=[]
#      for clusterName in getClustersInDomain():
#         actionedSvrListAll.append(controlResource(clusterName,'Cluster',actionType,'returnList'))
#      waitForJobCompletion(actionedSvrListAll,action,'auto')
#   finally:
#      if actionType == 'start':
#         verifyServers('StartStopped')
#      if actionType == 'stop':
#         verifyServers('StopRunning')
#      verifyServers('status')

def controlAllManServers(actionType):
   try:
      print '\n'+currTime()+' ['+domainName+'] Initiating '+actionType+' of all the managed servers in the Domain.'
      manServerList=getManServersInDomain()
      if msSkipFlag == 'YES':
         print currTime()+' [' + domainName+ '] Skipping following Servers: '+str(msSkipList)
         manServerList = list(pySet(manServerList) - pySet(msSkipList))
      if msStartFirstFlag == 'YES' and msStartLastFlag == 'YES' and actionType == 'start':
         manServerList = list(pySet(manServerList) - pySet(msStartFirstList))
         manServerList = list(pySet(manServerList) - pySet(msStartLastList))
         print 'The servers in ' + domainName + ' will be started in a specific order now: ' + str(msStartFirstList) + ' ' + str(manServerList) + ' ' + str(msStartLastList)
      elif msStartFirstFlag == 'YES' and msStartLastFlag != 'YES' and actionType == 'start':
         manServerList = list(pySet(manServerList) - pySet(msStartFirstList))
         print 'The servers in ' + domainName + ' will be started in a specific order now: ' + str(msStartFirstList) + ' ' + str(manServerList)
      elif msStartFirstFlag != 'YES' and msStartLastFlag == 'YES' and actionType == 'start':
         manServerList = list(pySet(manServerList) - pySet(msStartLastList))
         print 'The servers in ' + domainName + ' will be started in a specific order now: ' + str(manServerList) + ' ' + str(msStartLastList)

      if msStartFirstFlag == 'YES' and actionType == 'start':
         for svrName in msStartFirstList:
            controlResource(svrName,'Server',actionType,'NA')
         waitForJobCompletion(msStartFirstList,actionType,'auto')

      for svrName in manServerList:
         controlResource(svrName,'Server',actionType,'NA')
      waitForJobCompletion(manServerList,actionType,'auto')

      if msStartLastFlag == 'YES' and actionType == 'start':
         for svrName in msStartLastList:
            controlResource(svrName,'Server',actionType,'NA')
         waitForJobCompletion(msStartLastList,actionType,'auto')

   except Exception, e:
      dumpStack()
      print '[ERROR] ['+p_domainName+'] '+ str(e)
      #if actionType == 'start':
         #verifyServers('StartStopped')
      #if actionType == 'stop':
         #verifyServers('StopRunning')

def getAdminServerStatus(p_nmUser,p_nmPwd,p_domainName,p_hostName,p_nmPort,p_domainDir,p_nmType):
   for i in range(1,4):
      try:
         print currTime()+' [' + p_domainName + '] Connecting to Node Manager. Attempt # '+str(i)+' of 3.'
         j = i + 1
         if nmCredentialType == 'plain':
            nmConnect(username=p_nmUser, password=p_nmPwd, host=p_hostName, port=p_nmPort, domainName=p_domainName, domainDir=p_domainDir, nmType=p_nmType)
         elif nmCredentialType == 'encrypted':
            nmConnect(userConfigFile=p_nmUser, userKeyFile=p_nmPwd, host=p_hostName, port=p_nmPort, domainName=p_domainName, domainDir=p_domainDir, nmType=p_nmType)
         else:
            print '[ERROR] Incorrect nmCredentialType provided in prop file. It should be either [plain] or [encrypted].'
            exit()
         break
      except Exception, e:
         if j == 4:
            print currTime()+' [' + p_domainName + '] [ERROR] Could not connect to Node Manager. Giving up. Please check if Node Manager is up. Exiting.'
            exit()
         print '[ERROR] ['+p_domainName+'] '+ str(e)
         print currTime()+' [' + p_domainName + '] Waiting for 30 seconds before re-trying to connect with Node Manager...'
         pytime.sleep(30)
         continue
   #print currTime()+' [' + p_domainName + '] Getting Admin Server status...'
   adminStatus=nmServerStatus('AdminServer')
   print currTime()+' [' + p_domainName + '] Status of AdminServer: ' + str(adminStatus)
   return adminStatus

def controlAdminServer(p_nmUser,p_nmPwd,p_domainName,p_hostName,p_nmPort,p_domainDir,p_nmType,action):
   for i in range(1,4):
      try:
         print currTime()+' [' + p_domainName + '] Connecting to Node Manager. Attempt # '+str(i)+' of 3.'
         j = i + 1
         if nmCredentialType == 'plain':
            nmConnect(username=p_nmUser, password=p_nmPwd, host=p_hostName, port=p_nmPort, domainName=p_domainName, domainDir=p_domainDir, nmType=p_nmType)
         elif nmCredentialType == 'encrypted':
            nmConnect(userConfigFile=p_nmUser, userKeyFile=p_nmPwd, host=p_hostName, port=p_nmPort, domainName=p_domainName, domainDir=p_domainDir, nmType=p_nmType)
         else:
            print '[ERROR] Incorrect nmCredentialType provided in prop file. It should be either [plain] or [encrypted].'
            exit()
         break
      except Exception, e:
         if j == 4:
            print currTime()+' [' + p_domainName + '] [ERROR] Could not connect to Node Manager. Giving up. Please check if Node Manager is up. Exiting.'
            exit()
         print '[ERROR] ['+p_domainName+'] '+ str(e)
         print currTime()+' [' + p_domainName + '] Waiting for 30 seconds before re-trying to connect with Node Manager...'
         pytime.sleep(30)
         continue
   if action == 'stop':
      print currTime()+' [' + p_domainName + '] Stopping Admin Server...'
      nmKill('AdminServer')
      print currTime()+' [' + p_domainName + '] Status of AdminServer: ' + str(nmServerStatus('AdminServer'))
   elif action == 'start':
      currStatusAdmin = nmServerStatus('AdminServer')
      if currStatusAdmin == 'RUNNING' or currStatusAdmin == 'ADMIN':
        print currTime()+' [' + p_domainName+ '] Admin Server found to be in ['+currStatusAdmin+'] state already. Start will not be attempted.'
      else:
        print currTime()+' [' + p_domainName+ '] Starting Admin Server...'
        nmStart('AdminServer')
        currStatusAdmin = nmServerStatus('AdminServer')
        if currStatusAdmin != 'RUNNING':
           print currTime()+' [' + p_domainName + '] [ERROR] Admin Server did not start. Status: ' + str(currStatusAdmin)
        else:
           print currTime()+' [' + p_domainName + '] Status of AdminServer: RUNNING.'
   nmDisconnect()

def listComponents():
   domainConfig()
   print '\nListing Servers...\n'
   serverArray = cmo.getServers()
   for svr in serverArray:
      print svr.getName()
   print '\n\nListing Clusters...\n'
   clusterArray = cmo.getClusters()
   for clstr in clusterArray:
      print clstr.getName()

def verifyServers(action):
   print currTime()+' ['+domainName+'] Verifying server status...'
   serverList=getManServersInDomain()
   if msSkipFlag == 'YES':
      print currTime()+' [' + domainName+ '] Skipping following Servers: '+str(msSkipList)
      serverList = list(pySet(serverList) - pySet(msSkipList))
   domainRuntime()
   runningServersList = []
   stoppedServersList = []
   for serverName in serverList:
      cd('/ServerLifeCycleRuntimes/' + serverName)
      svrState= cmo.getState()
      if svrState == 'RUNNING':
         runningServersList.append(serverName)
         print ' ['+domainName+']  '+ str(serverName).ljust(35) + ':' + svrState
      elif svrState == 'SHUTDOWN':
         stoppedServersList.append(serverName)
         print ' ['+domainName+']  '+ str(serverName).ljust(35) + ':' + svrState 
      else:
         print ' ['+domainName+']  '+ str(serverName).ljust(35) + ':' + svrState
   #print '[Debug]:  RUNNING ManagedServers: ' + str(runningServersList).strip('[]')
   #print '[Debug]:  SHUTDOWN ManagedServers: ' + str(stoppedServersList).strip('[]')
   if action == 'StopRunning' and len(runningServersList) != 0:
      print "Stopping any of the servers that are still running..."
      print '[' + domainName + '] Servers still running: ' + str(runningServersList)
      for svr in runningServersList:
         print 'Stopping: ' + svr
         shutdown(svr, 'Server', force='true', ignoreSessions='true', block='false')
   elif action == 'StartStopped' and len(stoppedServersList) != 0:
      print "Starting any of the servers that are still down..."
      print '[' + domainName + '] Servers that are still down: ' + str(stoppedServersList)
      for svr in stoppedServersList:
         print 'Starting: ' + svr
         start(svr, 'Server', block='false')


def waitForJobCompletion(svrList,chkType,runType):
   if len(svrList) != 0:
      if chkType == 'stop':
         chkInterval=int(stopInterval)
         chkLoopLimit=int(stopLoopLimit)
      if chkType == 'start':
         chkInterval=int(startInterval)
         chkLoopLimit=int(startLoopLimit)
      print currTime()+' ['+domainName+'] Checking status of server(s) every ' + str(chkInterval) + ' secs for '+str(chkLoopLimit)+' iterations while they ' + chkType + '...'
      pytime.sleep(3)
      domainRuntime()
      cnt=1
      while true:
         statusList=[]
         #print '[Loop:'+ str(cnt) + ']'
         #print '[DEBUG] '+str(svrList)
         dispSvrStatus = currTime()+' ['+str(domainName)+'] [Loop:'+str(cnt) +'] '
         for svr in svrList:
            cd('/ServerLifeCycleRuntimes/' + svr)
            svrStatus=cmo.getState()
            #print ' ' + str(svr) + ': ' + str(svrStatus)
            dispSvrStatus = dispSvrStatus + '  ' + str(svr) + ':' + str(svrStatus)
            statusList.append(svrStatus)
         print dispSvrStatus
         #print 'DEBUG: ' + str(statusList)
         if chkType == 'start' and cnt < chkLoopLimit and 'STARTING' not in statusList and 'RESUMING' not in statusList and 'SHUTDOWN' not in statusList:
            print currTime()+' ['+domainName+'] Final Status: '+str(svrList)+' : '+str(statusList)
            break
         elif chkType == 'stop' and cnt < chkLoopLimit and 'SHUTTING DOWN' not in statusList and 'FORCE_SHUTTING_DOWN' not in statusList and 'SUSPENDING' not in statusList and 'FORCE_SUSPENDING' not in statusList and 'RUNNING' not in statusList:
            print currTime()+' ['+domainName+'] Final Status '+str(svrList)+' : '+str(statusList)
            break
         elif cnt >= chkLoopLimit:
            if runType == 'auto':
               print currTime()+' ['+domainName+'] [WARNING] Servers are taking too long to '+chkType+'. Moving to next item. The servers will continue to '+chkType+' in background.'
               break
            elif runType == 'manual':
               print currTime()+' ['+domainName+'] [WARNING] Servers are taking too long to '+chkType+'.'
               promptUser=raw_input('[PROMPT] Would you like to continue waiting?[y/n]: ')
               if promptUser == 'y' or promptUser == 'Y':
                  print '[INFO] Increasing the Iteration limit by 6'
                  chkLoopLimit = chkLoopLimit + 6
                  cnt += 1
               else:
                  break
         else:
            cnt += 1
            pytime.sleep(chkInterval)
   else:
      print currTime()+'[DEBUG] No elements in the list passed to function.'

def rollBounceAllManServers():
   print currTime()+' All servers in the domain will be stopped and started one by one.'
   serverList=getManServersInDomain()
   domainRuntime()
   for svrName in serverList:
      print '\n[RollBounce] Shutting down: ' + svrName
      shutdown(svrName, 'Server', force='true', ignoreSessions='true')
      pytime.sleep(5)
      print '[RollBounce] Starting up: ' + svrName
      start(svrName, 'Server', block='true')
      cd('/ServerLifeCycleRuntimes/' + svrName)
      svrState= cmo.getState()
      if svrState != 'RUNNING':
         print '[WARNING] Server [' + svrName + '] did not come into RUNNING status. Please check. The script has PAUSED RollBounce here.'
         promptUser=raw_input('[PROMPT] Would you like to continue by skipping this server or exit?[skip/exit]:')
         if promptUser == 'skip' or promptUser == 's':
            continue
         elif promptUser == 'exit' or promptUser == 'e':
            break
         else:
            print 'Invalid input. Script will exit now.'
            exit()

def rollBounceServersInClusterOneByOne(clstrName):
   print currTime()+' All servers in the '+clstrName+' cluster will be stopped and started one by one.'
   serverList=getManServersInCluster(clstrName)
   domainRuntime()
   for svrName in serverList:
      print '\n[RollBounce] Shutting down: ' + svrName
      shutdown(svrName, 'Server', force='true', ignoreSessions='true')
      pytime.sleep(5)
      print '\n[RollBounce] Starting Up: ' + svrName
      start(svrName, 'Server', block='true')
      cd('/ServerLifeCycleRuntimes/' + svrName)
      svrState= cmo.getState()
      if svrState != 'RUNNING':
         print '\n[WARNING] Server [' + svrName + '] did not come into RUNNING status. Please check. The script has PAUSED RollBounce here.'
         promptUser=raw_input('[PROMPT] Would you like to continue by skipping this server or exit?[skip/exit]:')
         if promptUser == 'skip' or promptUser == 's':
            continue
         elif promptUser == 'exit' or promptUser == 'e':
            break
         else:
            print 'Invalid input. Script will exit now.'
            exit()

def rollBounceServersInClusterInTwoParts(clstrName):
   allServerList=getManServersInCluster(clstrName)
   serverListEven=allServerList[::2]
   serverListOdd=allServerList[1::2]
   print currTime()+' ['+domainName+'] Initiating a roll bounce of servers in [' + clstrName + ']. The servers in this cluster have been divided into 2 parts...'
   print '       All servers in Part 1 will be stopped and started in parallel, followed by servers in Part 2.'
   print ' Part 1 servers are: ' + str(serverListEven)
   print ' Part 2 servers are: ' + str(serverListOdd)
   promptUser=raw_input('[PROMPT] Would you like to continue with the details above?[y/n]:')
   if promptUser == 'n' or promptUser == 'N' or promptUser == 'NO' or promptUser == 'no':
      print 'You have chosen to exit the script.'
      exit()
   print '\n[RollBounce] Shutting down following servers: ' + str(serverListEven)
   for svrName in serverListEven:
      controlResource(svrName,'Server','stop','NA')
   waitForJobCompletion(serverListEven,'stop','manual')
   print '\n[RollBounce] Starting up following servers: ' + str(serverListEven)
   for svrName in serverListEven:
      controlResource(svrName,'Server','start','NA')
   waitForJobCompletion(serverListEven,'start','manual')
   pytime.sleep(5)
   print '\n[RollBounce] Shutting down following servers: ' + str(serverListOdd)
   for svrName in serverListOdd:
      controlResource(svrName,'Server','stop','NA')
   waitForJobCompletion(serverListOdd,'stop','manual')
   print '\n[RollBounce] Starting up following servers: ' + str(serverListOdd)
   for svrName in serverListOdd:
      controlResource(svrName,'Server','start','NA')
   waitForJobCompletion(serverListOdd,'start','manual')
   pytime.sleep(5)
   print '\n'+currTime()+' ['+domainName+'] Roll Bounce of Cluster [' + clstrName + '] completed.'

def controlManSvrsOnHosts(actionType,hostList):
   actionedSvrList=[]
   print currTime()+' ['+domainName+'] Invoking ['+actionType+'] of managed servers on requested host(s): ['+str(hostList)+']'
   for svrName in getManServersInDomain():
      cd ('/Servers/'+svrName)
      svrHost=cmo.getListenAddress()
      svrHost=svrHost.strip()
      if svrHost == "":
         print currTime()+' ['+domainName+'] ['+ svrName+'] There is no Listen Address configured on this server. Skipping it. [WARNING]'
      else:
         if re.search(svrHost,hostList,re.IGNORECASE):
            print currTime()+' ['+domainName+'] ['+ svrName+'] ['+svrHost+'] : '+actionType+' requested.'
            actionedSvrList.append(svrName)
         else:
            print currTime()+' ['+domainName+'] ['+ svrName+'] ['+svrHost+'] : No action requested.'
   if len(actionedSvrList) != 0:
      for svrName in actionedSvrList:
         print '\n'+currTime()+' Invoking '+actionType+' of ['+svrName+']...'
         controlResource(svrName,'Server',actionType,'NA')
      waitForJobCompletion(actionedSvrList,actionType,'auto')

def getDetails(msString):
   domainConfig()
   allServerList=[]
   serverArray = cmo.getServers()
   for svr in serverArray:
      svrName=svr.getName()
      if (msString != ' ' and msString in svrName) or msString == ' ':
         allServerList.append(svrName)
   allServerList.sort()
   #print allServerList
   print '\n'+'SERVER_NAME'.ljust(32)+'SERVER_LISTEN_ADDR'.ljust(37)+'PORT'.ljust(6)+'STATE'.ljust(20)+'SERVER_START_TIME'.ljust(22)+'SVR_HEALTH'.ljust(24)+'OVERALL_HLTH'.ljust(24)+'HEAP_USED'
   for svrName in allServerList:
      domainConfig()
      cd('/Servers/'+ svrName)
      listenAddr=cmo.getListenAddress()
      if listenAddr == "":
         listenAddr='-'
      listenPort=cmo.getListenPort()
      domainRuntime()
      cd('/ServerLifeCycleRuntimes/'+ svrName)
      serverState= cmo.getState()
      if str(serverState) == 'RUNNING':
         cd('/ServerRuntimes/' + svrName)
         ServerActTime = pytime.strftime('%d-%b-%Y %H:%M:%S', pytime.localtime(cmo.getActivationTime()/1000))
         svrHealth=str(cmo.getHealthState())
         svrHealth=svrHealth.split(',')
         svrHealth=svrHealth[1].split(':')
         svrHealth=svrHealth[1]
         svrOverallHealth=str(cmo.getOverallHealthState())
         svrOverallHealth=svrOverallHealth.split(',')
         svrOverallHealth=svrOverallHealth[1].split(':')
         svrOverallHealth=svrOverallHealth[1]
         cd('/ServerRuntimes/' + svrName +'/JVMRuntime/' + svrName)
         heapFree = cmo.getHeapFreePercent()
         heapUsed = 100 - heapFree
         print str(svrName).ljust(32)+str(listenAddr).ljust(37)+str(listenPort).ljust(6)+str(serverState).ljust(20)+str(ServerActTime).ljust(22)+str(svrHealth).ljust(24)+str(svrOverallHealth).ljust(24)+str(heapUsed)+'%'
      else:
         print str(svrName).ljust(32)+str(listenAddr).ljust(37)+str(listenPort).ljust(10)+str(serverState).ljust(20)

def controlListOfManServers(actionType,msList):
   msListAll = getManServersInDomain()
   actionedSvrList=[]
   for svrName in msList:
      if svrName in msListAll:
         if actionType == 'status':
            print currTime()+' ['+domainName+'] Status of '+svrName+': '+getServerStatus(svrName)
         else:
            actionedSvrList = actionedSvrList + controlResource(svrName,'Server',actionType,'returnList')
      else:
         print currTime()+' ['+domainName+'] [WARNING] The Server [' + svrName + '] does not exist in this Domain.'
   if len(actionedSvrList) != 0:
      waitForJobCompletion(actionedSvrList,actionType,'auto')

def controlListOfClusters(actionType,clusterList):
   clusterListAll = getClustersInDomain()
   actionedSvrList=[]
   for clusterName in clusterList:
      if clusterName in clusterListAll:
         if actionType == 'status':
            print '\n'+currTime()+' ['+domainName+'] Displaying status of Servers in Cluster: '+clusterName+'.'
            for svrName in getManServersInCluster(clusterName):
               print currTime()+' ['+domainName+'] Status of '+svrName+': '+getServerStatus(svrName)
         else:
            actionedSvrList = actionedSvrList + controlResource(clusterName,'Cluster',actionType,'returnList')
      else:
         print currTime()+' ['+domainName+'] [WARNING] The Cluster [' + clusterName + '] does not exist in this Domain.'
   if len(actionedSvrList) != 0:
      waitForJobCompletion(actionedSvrList,actionType,'auto')


#===============Script Starts here==========================#
#M. Imran Ali

#Pass 'help' as the argument to get Syntax and also help related to the arguments to the script.
argslength = len(sys.argv) - 1
if sys.argv[1] == 'help':
   scriptSyntax()
   scriptHelp()
   exit()

#If no argument or less than required number of arguments is provided to the script, it will display syntax info.
if argslength < 3:
   print '[ERROR] Insufficient arguments.'
   scriptSyntax()
   exit()

#print '[INFO] Starting script at '+ pytime.ctime()

try:
   p_arg           = ' '
   p_propFilePrefix = sys.argv[1]
   p_domainName     = sys.argv[2]
   p_action         = sys.argv[3]
   if argslength == 4:
      p_arg         = sys.argv[4]
   #stopInterval    = 10                     #Time interval in seconds between Iterations during a stop action
   #startInterval   = 20                     #Time interval in seconds between Iterations during a start action
   #stopLoopLimit   = 3                      #The max number of iterations to check if server(s) stopped
   #startLoopLimit  = 5                      #The max number of iterations to check if server(s) started
   msStartFirst = 'NA'
   msStartLast = 'NA'
   msStartFirstFlag = 'NA'
   msStartLastFlag = 'NA'
   msSkipServers = 'NA'
   msSkipFlag = 'NA'

   argRequiredActionsList = ['stopManagedServers','startManagedServers','statusManagedServers','bounceManagedServers','stopClusters','startClusters','statusClusters','stopManServerContains','startManServerContains','stopClusterContains','startClusterContains','rollBounceClusterSerial','rollBounceCluster','stopManSvrsOnHosts','startManSvrsOnHosts']
   if p_action in argRequiredActionsList and argslength < 4:
      print '[ERROR] Insufficient Arguments. The ['+p_action+'] ACTION requires one more argument. See help.'
      exit()

   #Property File name is passed as argument. If you want to use a diff name using any specific env variable like $SID, use the commented out code chunk below this one.
   #p_propFile  = p_propFilePrefix+'.prop'
   p_propFile = 'properties/' + p_propFilePrefix + '.prop'
   if not os.path.isfile(p_propFile):
      print '[ERROR] The property file '+p_propFile+' was NOT found. Please check.'
      exit()

   #p_propFile  = str(os.environ['SID'])+'.prop'
   #if not os.path.isfile(p_propFile):
   #   print '[ERROR] The property file '+p_propFile+' was NOT found. Please check.'
   #   exit()

   #Checking if the domain name provided as arg matches the one in prop file. If not, prompt for input.
   while true:
      if p_domainName != 'exit' and p_domainName.lower() in open(p_propFile).read().lower():
         pfile=open(p_propFile, "r")
         for line in pfile.readlines():
            if line.find("adminServerHost") > 0:
               if re.search(p_domainName, line, re.IGNORECASE):
                  p_domainName=line.split('.')[1]
                  pfile.close()
                  break
         break
      elif p_domainName == 'exit':
         print currTime()+' Script will exit now.'
         exit()
      else:
         print '[ERROR] The Domain Name you provided does not match any of the domains listed in '+p_propFile
         p_domainName= raw_input('[PROMPT] Enter exact Domain Name (or exit):')
         print currTime()+' Domain Name provided: ['+ p_domainName + ']'

   #print '[INFO]                ['+p_domainName+'] Script started at '+ pytime.ctime()
   print currTime()+' ['+p_domainName+'] Script Started.'

   #The original wlst output to stdout is redirected to tmp.log file. Will help in troubleshooting.
   tempLog  = '/tmp/tmp_wlsControl_'+p_domainName+'.log'
   redirect(tempLog,'false')

   #Read the wls.prop file for Domain specific values
   propInputStream = FileInputStream(p_propFile)
   configProps = Properties()
   configProps.load(propInputStream)

   stopInterval=configProps.get('wls.scriptProp.stopInterval')
   startInterval=configProps.get('wls.scriptProp.startInterval')
   stopLoopLimit=configProps.get('wls.scriptProp.stopLoopLimit')
   startLoopLimit=configProps.get('wls.scriptProp.startLoopLimit')

   adminHost=configProps.get('wls.' + p_domainName + '.adminServerHost')
   adminPort=configProps.get('wls.' + p_domainName + '.adminServerPort')
   adminCredentialType=configProps.get('wls.' + p_domainName + '.adminCredentialType')
   adminUserName=configProps.get('wls.' + p_domainName + '.adminUserName')
   adminPassword=configProps.get('wls.' + p_domainName + '.adminPassword')
   wlsHome=configProps.get('wls.' + p_domainName + '.wlsHome')
   domainDir=configProps.get('wls.' + p_domainName + '.domainDir')
   nmPort=configProps.get('wls.' + p_domainName + '.nmPort')
   nmCredentialType=configProps.get('wls.' + p_domainName + '.nmCredentialType')
   nmUser=configProps.get('wls.' + p_domainName + '.nmUser')
   nmPassword=configProps.get('wls.' + p_domainName + '.nmPassword')
   nmType=configProps.get('wls.' + p_domainName + '.nmType')
   adminURL=str(adminHost) + ':' + str(adminPort)
   if p_domainName + '.serversToStartFirst' in open(p_propFile).read():
      msStartFirst=configProps.get('wls.' + p_domainName + '.serversToStartFirst')
      if msStartFirst != 'NA' and msStartFirst is not None:
         msStartFirstList = msStartFirst.split(",")
         msStartFirstFlag='YES'
   if p_domainName + '.serversToStartLast' in open(p_propFile).read():
      msStartLast=configProps.get('wls.' + p_domainName + '.serversToStartLast')
      if msStartLast != 'NA' and msStartLast is not None :
         msStartLastList = msStartLast.split(",")
         msStartLastFlag='YES'
   if p_domainName + '.serversToSkip' in open(p_propFile).read():
      msSkip=configProps.get('wls.' + p_domainName + '.serversToSkip')
      if msSkip != 'NA' and msSkip is not None:
         msSkipList = msSkip.split(",")
         msSkipFlag='YES'
   u_domainName=p_domainName
   if p_domainName + '.actualDomainName' in open(p_propFile).read():
      p_domainName=configProps.get('wls.' + p_domainName + '.actualDomainName')


#Start evaluating the Actions

   if 'AdminServer' in p_action or p_action == 'startAll':
      if p_action == 'statusAdminServer':
         getAdminServerStatus(nmUser,nmPassword,p_domainName,adminHost,nmPort,domainDir,nmType)
         nmDisconnect()
      elif p_action == 'startAdminServer':
         controlAdminServer(nmUser,nmPassword,p_domainName,adminHost,nmPort,domainDir,nmType,'start')
      elif p_action == 'stopAdminServer':
         controlAdminServer(nmUser,nmPassword,p_domainName,adminHost,nmPort,domainDir,nmType,'stop')
      elif p_action == 'startAll':
         controlAdminServer(nmUser,nmPassword,p_domainName,adminHost,nmPort,domainDir,nmType,'start')
         if adminCredentialType == 'plain':
            connect(username=adminUserName, password=adminPassword, url=adminURL)
         elif adminCredentialType == 'encrypted':
            connect(userConfigFile=adminUserName, userKeyFile=adminPassword, url=adminURL)
         else:
            print '[ERROR] Incorrect adminCredentialType provided in prop file. It should be either [plain] or [encrypted].'
            exit()
         controlAllManServers('start')
         disconnect()
      else:
          print '[ERROR] Invalid Action'
   else:
      if adminCredentialType == 'plain':
         connect(username=adminUserName, password=adminPassword, url=adminURL)
      elif adminCredentialType == 'encrypted':
         connect(userConfigFile=adminUserName, userKeyFile=adminPassword, url=adminURL)
      else:
         print '[ERROR] Incorrect adminCredentialType provided in prop file. It should be either [plain] or [encrypted].'
         exit()
      resourceName=p_arg
      resourceNameStr=p_arg
      hostList=p_arg
      if p_action == 'status':
         verifyServers('status')
      elif p_action == 'list':
         listComponents()
      elif p_action == 'details':
         getDetails(resourceNameStr)
      elif p_action == 'stopAll':
         controlAllManServers('stop')
         disconnect()
         controlAdminServer(nmUser,nmPassword,p_domainName,adminHost,nmPort,domainDir,nmType,'stop')
      elif p_action == 'restartAllManServers':
         controlAllManServers('stop')
         controlAllManServers('start')
      elif p_action == 'stopAllManServers':
         controlAllManServers('stop')
      elif p_action=='startAllManServers':
         controlAllManServers('start')
      elif p_action=='stopManagedServers':
         msList=resourceName.split(",")
         controlListOfManServers('stop',msList)
      elif p_action=='startManagedServers':
         msList=resourceName.split(",")
         controlListOfManServers('start',msList)
      elif p_action=='statusManagedServers':
         msList=resourceName.split(",")
         controlListOfManServers('status',msList)
      elif p_action=='bounceManagedServers':
         msList=resourceName.split(",")
         controlListOfManServers('stop',msList)
         controlListOfManServers('start',msList)
      elif p_action=='stopClusters':
         clusterList = resourceName.split(",")
         controlListOfClusters('stop',clusterList)
      elif p_action=='startClusters':
         clusterList = resourceName.split(",")
         controlListOfClusters('start',clusterList)
      elif p_action=='statusClusters':
         clusterList = resourceName.split(",")
         controlListOfClusters('status',clusterList)
      elif p_action=='stopManServerContains':
         controlMatchingResources(resourceNameStr,'Server','stop')
      elif p_action=='startManServerContains':
         controlMatchingResources(resourceNameStr,'Server','start')
      elif p_action=='stopClusterContains':
         controlMatchingResources(resourceNameStr,'Cluster','stop')
      elif p_action=='startClusterContains':
         controlMatchingResources(resourceNameStr,'Cluster','start')
      elif p_action=='rollBounceAllManServers':
         rollBounceAllManServers()
      elif p_action=='rollBounceClusterSerial':
         rollBounceServersInClusterOneByOne(resourceName)
      elif p_action=='rollBounceCluster':
         rollBounceServersInClusterInTwoParts(resourceName)
      elif p_action=='stopManSvrsOnHosts':
         controlManSvrsOnHosts('stop',hostList)
      elif p_action=='startManSvrsOnHosts':
         controlManSvrsOnHosts('start',hostList)
      else:
          print '[ERROR] Invalid Action'
#      disconnect()

except Exception, e:
   dumpStack()
   print currTime()+' ['+u_domainName+'] [ERROR] '+ str(e)

#print '[INFO]                ['+p_domainName+'] Script completed at '+ pytime.ctime()
print currTime()+' ['+u_domainName+'] Script Completed.'
exit()
