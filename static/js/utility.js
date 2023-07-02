function calculateTimeDifference(timestamp) {
    const datetimeValue = new Date(timestamp);
    const now = new Date();
    let diffMilliseconds = now - datetimeValue;

    // Calculate the time difference...
    let formattedTimeDifference = '';
    let isPast = true;

    if (diffMilliseconds < 0) {
        // The timestamp is in the past
        diffMilliseconds = Math.abs(diffMilliseconds);
        isPast = false;
    }

    const diffSeconds = Math.floor(diffMilliseconds / 1000);
    const diffMinutes = Math.floor(diffSeconds / 60);
    const diffHours = Math.floor(diffMinutes / 60);
    const diffDays = Math.floor(diffHours / 24);

    if (isPast) {
        if (diffDays > 0) {
        formattedTimeDifference = `${diffDays} day${diffDays > 1 ? 's' : ''} ago`;
        } else if (diffHours > 0) {
        formattedTimeDifference = `${diffHours} hour${diffHours > 1 ? 's' : ''} ago`;
        } else if (diffMinutes > 0) {
        formattedTimeDifference = `${diffMinutes} minute${diffMinutes > 1 ? 's' : ''} ago`;
        } else if (diffSeconds > 0) {
        formattedTimeDifference = `${diffSeconds} second${diffSeconds > 1 ? 's' : ''} ago`;
        }else {
        formattedTimeDifference = 'just now';
        }
    } else {
        if (diffDays > 0) {
        formattedTimeDifference = `in ${diffDays} day${diffDays > 1 ? 's' : ''}`;
        } else if (diffHours > 0) {
        formattedTimeDifference = `in ${diffHours} hour${diffHours > 1 ? 's' : ''}`;
        } else if (diffMinutes > 0) {
        formattedTimeDifference = `in ${diffMinutes} minute${diffMinutes > 1 ? 's' : ''}`;
        } else if (diffSeconds > 0) {
        formattedTimeDifference = `in ${diffSeconds} second${diffSeconds > 1 ? 's' : ''}`;
        } else {
        formattedTimeDifference = 'just now';
        }
    }

    return formattedTimeDifference;
    }

    function calculateTimeDifferenceSeconds(timestamp) {
    const datetimeValue = new Date(timestamp);
    const now = new Date();
    const diffMilliseconds = now - datetimeValue;

    const diffSeconds = Math.floor(diffMilliseconds / 1000);

    return diffSeconds;
}

function elideString(string) {
    if (string.length <= 12) {
        return string; // String is already within the desired length
    } else {
        return string.slice(0, 4) + "..." + string.slice(-5);
    }
}

function elideStringBack(string) {
    if (string.length <= 15) {
        return string; // String is already within the desired length
    } else {
        return string.slice(0, 15) + "..."
    }
}