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

    // Function to check if the screen width indicates a mobile device
    function isMobileDevice() {
        return window.innerWidth <= 768;
    }
    
    // Function to format time units
    function formatTimeUnit(value, unit) {
        if (value > 0) {
            return isMobileDevice() ? `${value}${unit.charAt(0)}` : `${value} ${unit}${value > 1 ? 's' : ''}`;
        } else {
            return 'just now';
        }
    }
    
    if (isPast) {
        if (diffDays > 0) {
            formattedTimeDifference = `${formatTimeUnit(diffDays, 'day')} ago`;
        } else if (diffHours > 0) {
            formattedTimeDifference = `${formatTimeUnit(diffHours, 'hour')} ago`;
        } else if (diffMinutes > 0) {
            formattedTimeDifference = `${formatTimeUnit(diffMinutes, 'minute')} ago`;
        } else if (diffSeconds > 0) {
            formattedTimeDifference = `${formatTimeUnit(diffSeconds, 'second')} ago`;
        } else {
            formattedTimeDifference = 'just now';
        }
    } else {
        if (diffDays > 0) {
            formattedTimeDifference = `in ${formatTimeUnit(diffDays, 'day')}`;
        } else if (diffHours > 0) {
            formattedTimeDifference = `in ${formatTimeUnit(diffHours, 'hour')}`;
        } else if (diffMinutes > 0) {
            formattedTimeDifference = `in ${formatTimeUnit(diffMinutes, 'minute')}`;
        } else if (diffSeconds > 0) {
            formattedTimeDifference = `in ${formatTimeUnit(diffSeconds, 'second')}`;
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

function formatNumber(value){
    try{
        return value.toLocaleString().replace(/\./g, ',')
    }
    catch(error){
        return ""
    }
}
