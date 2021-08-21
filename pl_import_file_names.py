import sublime
import sublime_plugin
import os
import re


folderExcludePatterns = None
fileExcludePatterns = None
pluginSettings = None
parentDirSymbol = '..'

def getPosition(view):
  return view.sel()[0].begin()

def find(array, filterFn):
  return next((el for el in array if filterFn(el)), None)

def some(array, filterFn):
  for el in array:
    if filterFn(el):
      return True
  return False

def every(array, filterFn):
  for el in array:
    if not filterFn(el):
      return False
  return True

def shouldIncludePath(path, excludePathPatterns):
  shouldIncludePathFn = lambda pattern: not re.search(re.escape(pattern).replace('\\*', '.*'), path)
  return every(excludePathPatterns, shouldIncludePathFn)

def getParentPath(path, parentLvl):
  if parentLvl == 0:
    return path
  root = path.split(os.sep)[0] if os.name == 'nt' else '/'
  parentPath = os.sep.join(path.split(os.sep)[0:-parentLvl])
  return parentPath if parentPath else root

def getRelativePath(rootDir, path):
  tmpPath = path.replace(rootDir, '');
  relativePath = tmpPath.replace(os.sep, '', 1) if tmpPath.startswith(os.sep) else tmpPath
  return relativePath.replace('\\', '/')

def plugin_loaded():
  global folderExcludePatterns, fileExcludePatterns, pluginSettings
  settings = sublime.load_settings('Preferences.sublime-settings')
  folderExcludePatterns = settings.get('folder_exclude_patterns')
  fileExcludePatterns = settings.get('file_exclude_patterns')
  pluginSettings = {
    "isHideExtensions": True,
    "extensions": ['.js', '.jsx', '.ts', '.tsx'],
    "useRelativePrefix": True,
  }
  tmpPattern = '|'.join(pluginSettings["extensions"]).replace('.', '\.')
  regexPattern = f'({tmpPattern})$'
  pluginSettings["extensionsRegex"] = re.compile(regexPattern)

class PathInputHandler(sublime_plugin.ListInputHandler):
  def __init__(self, currentDir, parentLvl = 0):
    self.currentDir = currentDir
    self.parentLvl = parentLvl

  def list_items(self):
    rootDir = getParentPath(self.currentDir, self.parentLvl)
    paths = [parentDirSymbol]

    def makeInputItem(path):
      if path == parentDirSymbol:
        return sublime.ListInputItem(parentDirSymbol, parentDirSymbol, '', 'Move To Upper Dir')
      isDirectory = path.endswith('/')
      annotation = 'Directory' if isDirectory else ''

      relativePathTitle = getRelativePath(rootDir, path)
      prefix = '../' * self.parentLvl
      if pluginSettings['useRelativePrefix']:
        prefix = './' if self.parentLvl == 0 else '../' * self.parentLvl
      suffix = relativePathTitle
      if pluginSettings['isHideExtensions']:
        suffix = pluginSettings["extensionsRegex"].sub('', relativePathTitle)
      relativePathValue = f'{prefix}{suffix}'
      return sublime.ListInputItem(relativePathTitle, relativePathValue, '', annotation)

    for root, dirs, files in os.walk(rootDir):
      for fileName in files:
        fullFileName = os.path.join(root, fileName)
        if shouldIncludePath(root, folderExcludePatterns) and shouldIncludePath(fullFileName, fileExcludePatterns):
          paths.append(fullFileName)
      for dirName in dirs:
        fullDirName = os.path.join(root, f'{dirName}/')
        if shouldIncludePath(fullDirName, folderExcludePatterns):
          paths.append(fullDirName)
    return map(makeInputItem, paths)

  def next_input(self, args):
    if args['path'] == parentDirSymbol:
      return PathInputHandler(self.currentDir, self.parentLvl + 1)
    return None

class ImportPathCommand(sublime_plugin.TextCommand):
  def run(self, edit, path):
    self.view.insert(edit, getPosition(self.view), path)
    
  def input(self, args):
    currentDir = os.path.dirname(self.view.file_name())
    return PathInputHandler(currentDir)

class OpenFileByPathCommand(sublime_plugin.TextCommand):
  def run(self, edit):
    view = self.view
    beginPoint = getPosition(view)
    currentDir = os.path.dirname(view.file_name())
    if not view.match_selector(beginPoint, 'string.quoted'): return

    pathRegion = view.extract_scope(beginPoint)
    relativePath = re.sub('("|\')', '', view.substr(pathRegion))
    if not relativePath: return

    path = os.path.join(currentDir, relativePath)
    if os.path.isfile(path):
      return view.window().open_file(path)
    elif pluginSettings['isHideExtensions']:
      existedExtension = find(pluginSettings['extensions'], lambda ext: os.path.isfile(f'{path}{ext}'))
      if existedExtension:
        return view.window().open_file(f'{path}{existedExtension}')
    sublime.status_message(f'Can\'t open file {path}')
