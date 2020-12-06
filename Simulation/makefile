LIBPKGS  = util wave gate parser sim
MAIN     = main

LIBCOMP  = sim parser gate wave util
LIBS     = $(addprefix -l, $(LIBCOMP))
LIBFILES = $(addsuffix .a, $(addprefix ../../lib/lib, $(LIBPKGS)))

EXEC     = GPUsimulator

all: libs main

libs:
	@for lib in $(LIBPKGS); \
	do \
		echo "Checking $$lib..."; \
		cd src/$$lib; \
			make -f make.$$lib --no-print-directory PKGNAME=$$lib; \
		cd ../../; \
	done

main:
	@echo "Checking $(MAIN)..."
	@cd ./src/$(MAIN);  \
		make -f make.$(MAIN) --no-print-directory INCLIB="$(LIBS)" EXEC=$(EXEC);


clean:
	@for lib in $(LIBPKGS); \
	do \
		echo "Cleaning $$lib..."; \
		cd ./src/$$lib; \
			make -f make.$$lib --no-print-directory PKGNAME=$$lib clean; \
		cd ../../; \
	done
	@echo "Cleaning $(MAIN)..."
	@cd ./src/$(MAIN); make -f make.$(MAIN) --no-print-directory clean
	@echo "Removing $(LIBFILES)..."
	@rm -f $(LIBFILES)
	@echo "Removing $(EXEC)..."
	@rm -f bin/$(EXEC) 