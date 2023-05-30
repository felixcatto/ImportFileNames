gitRepo = '/home/felix/web/ImportFileNames'

move-to-git:
	cp -r . $(gitRepo)

move-to-git-with-clear:
	find $(gitRepo) -mindepth 1 ! -regex '.*\.git.*' -delete
	cp -r . $(gitRepo)
