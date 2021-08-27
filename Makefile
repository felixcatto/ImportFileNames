gitRepo = '/home/felix/web/ImportFileNames'

move-to-git:
	find $(gitRepo) -mindepth 1 ! -regex '.*\.git.*' -delete
	cp -r . $(gitRepo)

