function multi_mex_runner(mex_url, access_token)
    sess = bq.Session(mex_url, access_token);
    try
        mexs = sess.mex.findNodes('/mex/mex');
        for i=1:length(mexs),
            mex = mexs{i};
            uri = mex.getAttribute('uri');
            r = regexp(uri,'/','split');
            access_token = r{end};
            fprintf('%d/%d - %s\n', i, length(mexs), uri);
            WatershedSegmentation(uri, access_token);
        end
        
        sess.finish();
    catch err
        ErrorMsg = [err.message, 10, 'Stack:', 10];
        for i=1:size(err.stack,1)
            ErrorMsg = [ErrorMsg, '     ', err.stack(i,1).file, ':', num2str(err.stack(i,1).line), ':', err.stack(i,1).name, 10];
        end
        sess.fail(ErrorMsg);
    end
end