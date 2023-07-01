# guess-email-owner


Given that the username part of an email is related to the owner's name, the task is to determine the owner of multiple emails based on English names.

The principle is that the username part of most email addresses is related to the owner's name, including abbreviations and variations. By enumerating and speculating on these possibilities, we can calculate the weight of the username part matching these features.

This approach is based on the idea from information theory that **"information is used to eliminate uncertainty."** The more information-rich the matching username part of the email is, the higher the certainty, while shorter names require less information to determine.
