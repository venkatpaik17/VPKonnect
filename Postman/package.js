// Use module.exports to export the functions that should be
// available to use from this package.
// module.exports = { <your_function> }

// Once exported, use this statement in your scripts to use the package.
// const myPackage = pm.require('<package_name>')

function getPostsResponse(responseJson) {
    if (pm.response.code === 200) {
        if (responseJson.hasOwnProperty('access_token')){
            pm.environment.set('JWT', responseJson.access_token);
            console.log('Token refreshed. Re-send request.');
            return;
        }

        let allPosts = pm.environment.get('allPosts');
        if (allPosts) {
            try {
                allPosts = JSON.parse(allPosts);

                if (!Array.isArray(allPosts)) {
                    throw new Error('Stored data is not an array');
                }
            } catch (e) {
                console.error('Error parsing allPosts:', e);
                allPosts = [];
            }
        } else {
            allPosts = [];
        }

        if (responseJson.hasOwnProperty('message')){
            console.log(responseJson);
            if (responseJson.hasOwnProperty('info') && responseJson.info === "Done"){
                if (allPosts.length > 0) {
                    console.log(allPosts);
                    pm.environment.unset('allPosts');
                    pm.environment.unset('lastPostId');
                }
            }
            return;
        }
        
        if (!Array.isArray(responseJson)) {
            console.error('Response is not an array:', responseJson);
            return; 
        }

        const lastPost = responseJson[responseJson.length - 1];
        const lastPostId = lastPost.id;

        // console.log('Last post:', lastPost);
        console.log('Last post ID:', lastPostId);
        allPosts = allPosts.concat(responseJson);

        pm.environment.set('lastPostId', lastPostId);
        pm.environment.set('allPosts', JSON.stringify(allPosts));

        if (allPosts.length > 0) {
            console.log(allPosts);
        } else {
            console.log([]);
        }
    } else {
        const errorDetail = {
            status: `${pm.response.code} ${pm.response.status}`,
            detail: responseJson.detail || 'No detail provided'
        };
        console.error('Error fetching user posts:', errorDetail);
    }
}

function getAllFeedPostsResponse(responseJson) {
    if (pm.response.code === 200) {
        if (responseJson.hasOwnProperty('access_token')){
            pm.environment.set('JWT', responseJson.access_token);
            console.log('Token refreshed. Re-send request.');
            return;
        }

        if (responseJson.hasOwnProperty('message')){
            console.log(responseJson);
            pm.environment.unset('allFeedPosts');
            pm.environment.unset('lastSeenPostId');
            return;
        }
        
        if (responseJson.hasOwnProperty('posts') && Array.isArray(responseJson.posts)) {
            const posts = responseJson.posts;
            const lastSeenPostId = responseJson.next_cursor;

            let allFeedPosts = pm.environment.get('allFeedPosts');
            if (allFeedPosts) {
                try {
                    allFeedPosts = JSON.parse(allFeedPosts);

                    if (!Array.isArray(allFeedPosts)) {
                        throw new Error('Stored data is not an array');
                    }
                } catch (e) {
                    console.error('Error parsing allFeedPosts:', e);
                    allFeedPosts = [];
                }
            } else {
                allFeedPosts = []; 
            }

            pm.environment.set('lastSeenPostId', lastSeenPostId);
            console.log('Last Seen Post ID:', lastSeenPostId);

            allFeedPosts = allFeedPosts.concat(posts);
            pm.environment.set('allFeedPosts', JSON.stringify(allFeedPosts));

            if (allFeedPosts.length > 0) {
                console.log(allFeedPosts);
            } else {
                console.log([]);
            }
        } else {
            console.error('Response does not contain an array of posts or posts is missing:', responseJson);
        }
    } else {
        const errorDetail = {
            status: `${pm.response.code} ${pm.response.status}`,
            detail: responseJson.detail || 'No detail provided'
        };
        console.error('Error fetching user feed:', errorDetail);
    }
}

function getAllPostLikeUsersResponse(responseJson){
    if (pm.response.code === 200) {
        if (responseJson.hasOwnProperty('access_token')){
            pm.environment.set('JWT', responseJson.access_token);
            console.log('Token refreshed. Re-send request.');
            return;
        }

        let allLikeUsers = pm.environment.get('allLikeUsers');
        if (allLikeUsers) {
            try {
                allLikeUsers = JSON.parse(allLikeUsers);

                if (!Array.isArray(allLikeUsers)) {
                    throw new Error('Stored data is not an array');
                }
            } catch (e) {
                console.error('Error parsing allLikeUsers:', e);
                allLikeUsers = [];
            }
        } else {
            allLikeUsers = []; 
        }

        if (responseJson.hasOwnProperty('message')){
            console.log(responseJson);
            if (responseJson.hasOwnProperty('info') && responseJson.info === "Done"){
                if (allLikeUsers.length > 0){
                    console.log(allLikeUsers);
                    pm.environment.unset('allLikeUsers');
                    pm.environment.unset('lastLikeUserId');
                }
            }
            return;
        }
        
        if (responseJson.hasOwnProperty('like_users') && Array.isArray(responseJson.like_users)) {
            const likeUsers = responseJson.like_users;
            const lastLikeUserId = responseJson.next_cursor;

            pm.environment.set('lastLikeUserId', lastLikeUserId);
            console.log('Last Like User ID:', lastLikeUserId);

            allLikeUsers = allLikeUsers.concat(likeUsers);
            pm.environment.set('allLikeUsers', JSON.stringify(allLikeUsers));

            if (allLikeUsers.length > 0) {
                console.log(allLikeUsers);
            } else {
                console.log([]);
            }
        } else {
            console.error('Response does not contain an array of like users or like_users is missing:', responseJson);
        }
    } else {
        const errorDetail = {
            status: `${pm.response.code} ${pm.response.status}`,
            detail: responseJson.detail || 'No detail provided'
        };
        console.error('Error fetching post like users:', errorDetail);
    }
}

function getAllCommentsResponse(responseJson){
    if (pm.response.code === 200) {
        if (responseJson.hasOwnProperty('access_token')){
            pm.environment.set('JWT', responseJson.access_token);
            console.log('Token refreshed. Re-send request.');
            return;
        }

        let allComments = pm.environment.get('allComments');
        if (allComments) {
            try {
                allComments = JSON.parse(allComments);

                if (!Array.isArray(allComments)) {
                    throw new Error('Stored data is not an array');
                }
            } catch (e) {
                console.error('Error parsing allComments:', e);
                allComments = [];
            }
        } else {
            allComments = []; 
        }
        
        if (responseJson.hasOwnProperty('message')){
            console.log(responseJson);
            if (responseJson.hasOwnProperty('info') && responseJson.info === "Done"){
                if (allComments.length > 0){
                    console.log(allComments);
                    pm.environment.unset('allComments');
                    pm.environment.unset('lastCommentId');
                }
            }
            return;
        }
        
        if (responseJson.hasOwnProperty('comments') && Array.isArray(responseJson.comments)) {
            const comments = responseJson.comments;
            const lastCommentId = responseJson.next_cursor;

            pm.environment.set('lastCommentId', lastCommentId);
            console.log('Last Comment ID:', lastCommentId);

            allComments = allComments.concat(comments);
            pm.environment.set('allComments', JSON.stringify(allComments));

            if (allComments.length > 0) {
                console.log(allComments);
            } else {
                console.log([]);
            }
        } else {
            console.error('Response does not contain an array of comments or comments is missing:', responseJson);
        }
    } else {
        const errorDetail = {
            status: `${pm.response.code} ${pm.response.status}`,
            detail: responseJson.detail || 'No detail provided'
        };
        console.log('Error fetching comments:', errorDetail);
    }
}

function getAllCommentLikeUsersResponse(responseJson){
    if (pm.response.code === 200) {
        if (responseJson.hasOwnProperty('access_token')){
            pm.environment.set('JWT', responseJson.access_token);
            console.log('Token refreshed. Re-send request.');
            return;
        }

        let allLikeUsers = pm.environment.get('allLikeUsers');
        if (allLikeUsers) {
            try {
                allLikeUsers = JSON.parse(allLikeUsers);

                if (!Array.isArray(allLikeUsers)) {
                    throw new Error('Stored data is not an array');
                }
            } catch (e) {
                console.error('Error parsing allLikeUsers:', e);
                allLikeUsers = [];
            }
        } else {
            allLikeUsers = []; 
        }
        
        if (responseJson.hasOwnProperty('message')){
            console.log(responseJson);
            if (responseJson.hasOwnProperty('info') && responseJson.info === "Done"){
                if (allLikeUsers.length > 0){
                    console.log(allLikeUsers);
                    pm.environment.unset('allLikeUsers');
                    pm.environment.unset('lastLikeUserId');
                }
            }
            return;
        }
        
        if (responseJson.hasOwnProperty('like_users') && Array.isArray(responseJson.like_users)) {
            const likeUsers = responseJson.like_users;
            const lastLikeUserId = responseJson.next_cursor;

            pm.environment.set('lastLikeUserId', lastLikeUserId);
            console.log('Last Like User ID:', lastLikeUserId);

            allLikeUsers = allLikeUsers.concat(likeUsers);
            pm.environment.set('allLikeUsers', JSON.stringify(allLikeUsers));

            if (allLikeUsers.length > 0) {
                console.log(allLikeUsers);
            } else {
                console.log([]);
            }
        } else {
            console.error('Response does not contain an array of like users or like_users is missing:', responseJson);
        }
    } else {
        const errorDetail = {
            status: `${pm.response.code} ${pm.response.status}`,
            detail: responseJson.detail || 'No detail provided'
        };
        console.log('Error fetching comment like users:', errorDetail);
    }
}

module.exports = { 
    getPostsResponse,
    getAllFeedPostsResponse,
    getAllPostLikeUsersResponse,
    getAllCommentsResponse,
    getAllCommentLikeUsersResponse
};
