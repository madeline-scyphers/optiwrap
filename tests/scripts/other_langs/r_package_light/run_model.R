library(jsonlite)
source("../r_utils/hartman6.R")

# Additional printing and sleeping for unit testing
print("R script started running.")
Sys.sleep(2)

# This is where we read in from BOA the command line argument.
# If in your script, you use any other command line arguments,
# generally BOA's trial_dir should be the last command line arugment,
# But in this case, because of testing, we have deliberately added
# it as the first command line argument as well for testing.
args <- commandArgs(trailingOnly=TRUE)
trial_dir <- args[1]

param_path <- file.path(trial_dir, "parameters.json")
data <- read_json(path=param_path)

# We pull these from command line arguments defined from jinja2 template in the config
# to test that we can for testing
x0 <- as.numeric(args[2])
x1 <- as.numeric(args[3])

x2 <- data$x2
x3 <- data$x3
x4 <- data$x4
x5 <- data$x5
X <- c(x0, x1, x2, x3, x4, x5)

res <- hartman6(X)
if (!is.na(res)) {
    out_data <- list(
        TrialStatus=unbox("COMPLETED")
    )
    json_data <- toJSON(out_data, pretty = TRUE)
    write(json_data, file.path(trial_dir, "TrialStatus.json"))


    out_data <- list(
        metric=res,
        l2norm=sum(X**2)**(1/2)
    )

    json_data <- toJSON(out_data, pretty = TRUE)
    write(json_data, file.path(trial_dir, "output.json"))
} else {
    out_data <- list(
        TrialStatus=unbox("FAILED")
    )
    json_data <- toJSON(out_data, pretty = TRUE)
    write(json_data, file.path(trial_dir, "TrialStatus.json"))
}
# Additional printing for unit testing
print("R script finished running.")
