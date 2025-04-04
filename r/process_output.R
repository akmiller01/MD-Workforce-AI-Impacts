list.of.packages <- c(
  "data.table", "dplyr", "tidyverse", "openxlsx", "ggplot2", "scales", "stringr"
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

# Load results
results = fread("output/all_occupation_task_ratings.csv", encoding="UTF-8")
results_agg = results[,.(
  percent_of_tasks_average_or_better=sum(rating >= 3) / .N,
  percent_of_tasks_assisted_or_better=sum(rating >= 2) / .N,
  mean_rating=mean(rating)
), by=.(occupation_title)]

industries = fread("input/all_occupation_titles_industry.csv", encoding="UTF-8")
setnames(industries, "occupation_title", "OCC_TITLE")

detailed_occupations = merge(detailed_occupations, industries, by="OCC_TITLE")

# Categories
## High automation risk (50% or more of your tasks can be done at average human level or better by AI)
## High augmentation potential (Less than 50% of your tasks can be done at average human level, but 50% or more of your tasks can be done by AI with human assistance)
## Low augmentation potential (Less than 50% of your tasks can be done at the average human level and less than 50% of your tasks can be done by AI with human assistance)

results_agg$label = NA
results_agg$label[which(
  results_agg$percent_of_tasks_average_or_better >= 0.50
)] = "high_automation_risk"

results_agg$label[which(
  results_agg$percent_of_tasks_average_or_better < 0.50 &
    results_agg$percent_of_tasks_assisted_or_better >= 0.50
)] = "high_augmentation_potential"

results_agg$label[which(
  results_agg$percent_of_tasks_average_or_better < 0.50 &
    results_agg$percent_of_tasks_assisted_or_better < 0.50
)] = "low_risk_potential"

results_table = data.frame(table(results_agg$label))
names(results_table) = c("label", "count")
fwrite(results_table, "output/occupation_results_table.csv")

setnames(results_agg, "occupation_title", "OCC_TITLE")

detailed_occupations = merge(detailed_occupations, results_agg, by="OCC_TITLE")

automatability_by_state = data.table(detailed_occupations)[,.(
  TOT_EMP=sum(TOT_EMP, na.rm=T)
), by=.(AREA, AREA_TITLE, label)]

automatability_by_state_wide = dcast(
  automatability_by_state, AREA+AREA_TITLE~label, value.var="TOT_EMP"
)

automatability_by_state_wide$total_occupations = rowSums(
  automatability_by_state_wide[,c("high_automation_risk", "high_augmentation_potential", "low_risk_potential")]
)

automatability_by_state_wide$high_automation_risk_pct =
  automatability_by_state_wide$high_automation_risk /
  automatability_by_state_wide$total_occupations

automatability_by_state_wide$high_augmentation_potential_pct =
  automatability_by_state_wide$high_augmentation_potential /
  automatability_by_state_wide$total_occupations

automatability_by_state_wide$low_risk_potential_pct =
  automatability_by_state_wide$low_risk_potential /
  automatability_by_state_wide$total_occupations

risk_dat = automatability_by_state_wide[,c("AREA_TITLE", "high_automation_risk_pct")]
risk_dat = risk_dat[order(-risk_dat$high_automation_risk_pct),]
risk_dat$AREA_TITLE = factor(risk_dat$AREA_TITLE, levels=risk_dat$AREA_TITLE)
risk_dat$fill = "#3C4586"
risk_dat$fill[which(risk_dat$AREA_TITLE=="Maryland")] = "#C84A35"

ggplot(risk_dat, aes(x=AREA_TITLE, y=high_automation_risk_pct, fill=fill)) +
  geom_bar(stat="identity") +
  scale_fill_identity() +
  scale_y_continuous(expand = c(0, 0), label=percent) +
  expand_limits(y=c(0, max(risk_dat$high_automation_risk_pct)*1.1)) +
  theme_bw() +
  theme(
    panel.border = element_blank()
    ,panel.grid.major.x = element_blank()
    ,panel.grid.minor.x = element_blank()
    ,panel.grid.major.y = element_line(colour = "grey80")
    ,panel.grid.minor.y = element_blank()
    ,panel.background = element_blank()
    ,plot.background = element_blank()
    ,axis.line.x = element_line(colour = "black")
    ,axis.line.y = element_blank()
    ,axis.ticks = element_blank()
    ,legend.position = "bottom"
    ,axis.text.x = element_text(angle = 45, vjust = 1, hjust=1)
  ) +
  labs(
    y="Percent of workforce",
    x="",
    title="Workforce at high automation risk"
  )
ggsave("output/risk_by_state.png", width=15, height=5)

md = subset(detailed_occupations, AREA_TITLE=="Maryland")

md_dat = md[,c("OCC_TITLE", "TOT_EMP", "label")]
md_dat$label[which(md_dat$label=="high_automation_risk")] = "High automation risk"
md_dat$label[which(md_dat$label=="high_augmentation_potential")] = "High augmentation potential"
md_dat$label[which(md_dat$label=="low_risk_potential")] = "Low risk/potential"
md_dat$label = factor(md_dat$label, levels=c(
  "High automation risk",
  "High augmentation potential",
  "Low risk/potential"
))
md_dat = md_dat[order(-md_dat$TOT_EMP),]
md_dat$OCC_TITLE = factor(md_dat$OCC_TITLE, levels=md_dat$OCC_TITLE)

md_dat = md_dat[c(1:15),]

ggplot(md_dat, aes(x=OCC_TITLE, y=TOT_EMP, fill=label)) +
  geom_bar(stat="identity") +
  scale_fill_manual(values=c("#C84A35", "#EDC5BD", "#3C4586")) +
  scale_y_continuous(expand = c(0, 0), label=number_format(big.mark=",")) +
  scale_x_discrete(labels = function(x) str_wrap(x, width = 30)) +
  expand_limits(y=c(0, max(md_dat$TOT_EMP)*1.1)) +
  theme_bw() +
  theme(
    panel.border = element_blank()
    ,panel.grid.major.x = element_blank()
    ,panel.grid.minor.x = element_blank()
    ,panel.grid.major.y = element_line(colour = "grey80")
    ,panel.grid.minor.y = element_blank()
    ,panel.background = element_blank()
    ,plot.background = element_blank()
    ,axis.line.x = element_line(colour = "black")
    ,axis.line.y = element_blank()
    ,axis.ticks = element_blank()
    ,legend.position = "bottom"
    ,axis.text.x = element_text(angle = 45, vjust = 1, hjust=1)
  ) +
  labs(
    y="Total employees",
    x="",
    fill="",
    title="Top 15 occupations in Maryland by automation risk (2023)"
  )
ggsave("output/md_top_occupations.png", width=15, height=5)

md$industry_classification[which(md$industry_classification=="None of the above")] = "All other industries"

md_by_lighthouse = data.table(md)[,.(
  TOT_EMP=sum(TOT_EMP, na.rm=T)
), by=.(industry_classification, label)]

md_by_lighthouse_wide = dcast(
  md_by_lighthouse, industry_classification~label, value.var="TOT_EMP"
)
md_by_lighthouse_wide$high_automation_risk[which(is.na(md_by_lighthouse_wide$high_automation_risk))] = 0
md_by_lighthouse_wide$high_augmentation_potential[which(is.na(md_by_lighthouse_wide$high_augmentation_potential))] = 0
md_by_lighthouse_wide$low_risk_potential[which(is.na(md_by_lighthouse_wide$low_risk_potential))] = 0

md_by_lighthouse_wide$total_occupations = rowSums(
  md_by_lighthouse_wide[,c("high_automation_risk", "high_augmentation_potential", "low_risk_potential")]
)

md_by_lighthouse_wide$high_automation_risk_pct =
  md_by_lighthouse_wide$high_automation_risk /
  md_by_lighthouse_wide$total_occupations

md_by_lighthouse_wide$high_augmentation_potential_pct =
  md_by_lighthouse_wide$high_augmentation_potential /
  md_by_lighthouse_wide$total_occupations

md_by_lighthouse_wide$low_risk_potential_pct =
  md_by_lighthouse_wide$low_risk_potential /
  md_by_lighthouse_wide$total_occupations

md_by_lighthouse_wide = md_by_lighthouse_wide[order(md_by_lighthouse_wide$industry_classification=="All other industries",-md_by_lighthouse_wide$high_automation_risk_pct),]

md_by_lighthouse_long = melt(
  md_by_lighthouse_wide,
  id.vars=c("industry_classification"),
  measure.vars=c("high_automation_risk_pct", "high_augmentation_potential_pct", "low_risk_potential_pct")
)

md_by_lighthouse_long$label = NA
md_by_lighthouse_long$label[which(md_by_lighthouse_long$variable=="high_automation_risk_pct")] = "High automation risk"
md_by_lighthouse_long$label[which(md_by_lighthouse_long$variable=="high_augmentation_potential_pct")] = "High augmentation potential"
md_by_lighthouse_long$label[which(md_by_lighthouse_long$variable=="low_risk_potential_pct")] = "Low risk/potential"
md_by_lighthouse_long$label = factor(md_by_lighthouse_long$label, levels=c(
  "Low risk/potential",
  "High augmentation potential",
  "High automation risk"
))
md_by_lighthouse_long$industry_classification = factor(
  md_by_lighthouse_long$industry_classification, 
  levels=md_by_lighthouse_wide$industry_classification)


ggplot(md_by_lighthouse_long, aes(x=industry_classification, y=value, group=label, fill=label)) +
  geom_bar(stat="identity") +
  scale_fill_manual(values=c("#3C4586", "#EDC5BD", "#C84A35"), guide = guide_legend(reverse = TRUE)) +
  scale_y_continuous(expand = c(0, 0), label=percent) +
  theme_bw() +
  theme(
    panel.border = element_blank()
    ,panel.grid.major.x = element_blank()
    ,panel.grid.minor.x = element_blank()
    ,panel.grid.major.y = element_line(colour = "grey80")
    ,panel.grid.minor.y = element_blank()
    ,panel.background = element_blank()
    ,plot.background = element_blank()
    ,axis.line.x = element_line(colour = "black")
    ,axis.line.y = element_blank()
    ,axis.ticks = element_blank()
    ,legend.position = "bottom"
    ,axis.text.x = element_text(angle = 45, vjust = 1, hjust=1)
  ) +
  labs(
    y="Percent of current workforce\nin lighthouse industry",
    x="",
    fill="",
    title="Maryland lighthouse industries by automation/augmentation class"
  )
ggsave("output/md_by_industry.png", width=8, height=5)

