list.of.packages <- c(
  "data.table", "dplyr", "tidyverse", "openxlsx"
)
new.packages <- list.of.packages[!(list.of.packages %in% installed.packages()[,"Package"])]
if(length(new.packages)) install.packages(new.packages)
suppressPackageStartupMessages(lapply(list.of.packages, require, character.only=T))

setwd("C:/git/MD-Workforce-AI-Impacts/")

# Downloaded from https://www.bls.gov/oes/current/oes_md.htm
dat = read.xlsx(
  "input/state_M2023_dl.xlsx",
  na.strings=c("", "*", "**", "#")
)

detailed_occupations = subset(dat, O_GROUP=="detailed")

all_occupation_titles = data.frame(occupation_title=unique(detailed_occupations$OCC_TITLE))
fwrite(all_occupation_titles, "input/all_occupation_titles.csv")
